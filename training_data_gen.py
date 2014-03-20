from face_finder import *
import numpy
import random
import copy
import csv
import glob



class training_data_gen():

    def __init__(self):
        self.ff = FaceFinder()


    def draw_plus(self, image, coord, width=20, color=(0,0,255)):    
        img_size = numpy.shape(image)

        # note: aguments of the CvPoint type must be tuples and not lists
        cv2.line(image, tuple(map(int, numpy.around((coord[0], coord[1]-width/2)))), tuple(map(int, numpy.around((coord[0], coord[1]+width/2)))), color)
        cv2.line(image, tuple(map(int, numpy.around((coord[0]-width/2, coord[1])))), tuple(map(int, numpy.around((coord[0]+width/2, coord[1])))), color)


    def in_eye_box(self, (pupx, pupy), eyes):
        for (ex,ey,ew,eh) in eyes:
            if pupx > ex and pupx < ex+ew and pupy > ey and pupy < ey+eh:
                return True
        if True:
            return False


    def write_eye_data(self, eyes, trainingfacefile, image, pupil_coords, subimg_num=''):
        for idx,(ex,ey,ew,eh) in enumerate(eyes):

            # deepcopying a separate object for annotation seems to be necessary:
            # TODO: later, loop over clean face and annotated face earlier so you don't need to copy each time
            image_annotated = copy.deepcopy(image)

            filename = './training_data_processed/'+os.path.splitext(os.path.basename(trainingfacefile))[0]+'_eye'+str(idx)+'_'+subimg_num
            # write eye image without annotation:
            eye_imfile = filename+'.jpg'
            cv2.imwrite(eye_imfile, image[ey:ey+eh, ex:ex+ew])

            # draw pre-annotated pupil coordinates:
            # (use named tuples eventually)
            self.draw_plus(image_annotated, pupil_coords[0])
            self.draw_plus(image_annotated, pupil_coords[1])

            # write eye image with annotation:
            eye_clean_imfile = filename+'_landmarked.jpg'
            cv2.imwrite(eye_clean_imfile, image_annotated[ey:ey+eh, ex:ex+ew])

            # convert the pupil coords to ([-1, +1], [-1, +1]) interval & write to file:
            pupil_coords_mapped = ((pupil_coords[idx][0]-ex)/ew*2-1,  (pupil_coords[idx][1]-ey)/eh*2-1)
            pupcoordfile = open(filename+'.eye','w')
            pupcoordfile.write('# pupil coords on [-1,+1], [-1,+1] interval \n')
            writer = csv.writer(pupcoordfile, delimiter='\t')
            writer.writerow(pupil_coords_mapped)
            pupcoordfile.close()



    def make_training_data(self, training_data_folder_raw, training_data_folder_processed, maxjitx=10):

        maxjity = 0.5*maxjitx

        training_data_filelist = glob.glob(training_data_folder_raw+"/*pgm")
        for trainingfacefile in training_data_filelist:

            # TODO: print a running status to the terminal of what face you are on of the total

            # (not sure why the second arg is necessary, since the images are gray to start with)
            image = cv2.imread(trainingfacefile, cv2.CV_LOAD_IMAGE_GRAYSCALE)

            # read in landmarked pupil coords, reverse them so 0=left eye on image, 1=right eye on image:
            pupil_coords = numpy.genfromtxt(os.path.splitext(trainingfacefile)[0]+'.eye')
            pupil_coords = [pupil_coords[2:4], pupil_coords[0:2]]

            # search for a face on the image using OpenCV subroutines:
            f = self.ff.find_face(cv.fromarray(image))
            if f:
                # search for eyes on the face using OpenCV subroutines:
                eyes = self.ff.find_eyes(cv.fromarray(image), f)

                # for training, only use the images where 2 eye boxes are found, and check that the "landmarked" pupil coordinates lie within these boxes
                # TODO: allow for 1 eye only to be found (though, note that sometimes 2 boxes find the same eye. can this be specified against in OpenCV coords?)
                num_eyes_found = numpy.shape(eyes)[0]
                if num_eyes_found == 2:

                    if self.in_eye_box(pupil_coords[0], eyes) and self.in_eye_box(pupil_coords[1], eyes):

                        # sort the eyes, so you can index left and right:
                        eyes = eyes[numpy.argsort(eyes[:,0])]

                        # write the un-jittered, original eye images:
                        self.write_eye_data(eyes, trainingfacefile, image, pupil_coords, ('%04d' % 1))

                        # generate 99 jitterings of the eye to artificially expand the data set:
                        for i in range(2,11):
                            jitterleft  = eyes[0] + numpy.array((random.randint(-maxjitx,maxjitx), random.randint(-maxjity,maxjity), 0, 0))
                            jitterright = eyes[1] + numpy.array((random.randint(-maxjitx,maxjitx), random.randint(-maxjity,maxjity), 0, 0))
                            self.write_eye_data((jitterleft, jitterright), trainingfacefile, image, pupil_coords, ('%04d' % i))

                    else:
                        print 'image not found, or not usable' 


