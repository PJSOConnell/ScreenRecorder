import os, time, re
from timeit import default_timer
from datetime import timedelta
import cv2
from PIL import Image
from io import BytesIO
import numpy as np
import shutil
import pyautogui
import glob
import threading
from loguru import logger


class ScreenRecord:
    """
    @params:
        driver         - Required  : WebDriver object (WebDriver)
        file_path_root - Optional  : Path representing a file path for output (Path)
        file_name      - Optional  : String representing a file name for output (Str)
        video_format   - Optional  : String specifying output format of video - mp4/avi (Str)
        fps            - Optional  : int representing frames per second (experimental) (Int)
    """
    def __init__(self, **kwargs):
        self.logger = kwargs.get("logger", logger)
        self.driver = kwargs.get("driver", None)
        self.file_path_root = kwargs.get("file_path_root", None)
        self.file_name = kwargs.get("file_name", "output")
        self.video_format = kwargs.get("video_format", "mp4")
        self.fps = int(kwargs.get("fps", 4))
        self.record = False

    def stop_recording(self, cleanup=True):
        """
            @params:
                cleanup      - Optional  : Determines if verification and temp file delete occurs (default is True) (Boolean)
        """
        if self.record:
            self.record = False
            time.sleep(2)
            if cleanup:
                current_file, temp_location = self.__generate_file_and_temp_location()
                if hasattr(self, "imgs"):
                    if self.imgs:
                        if not os.path.exists(temp_location):
                            os.makedirs(temp_location)
                        self.write_file_list_to_video_file(self.imgs, output_file=current_file,
                                                           temp_location=temp_location)
                        self.validate_video_creation(current_file, temp_location)
                        delattr(self, "imgs")
            else:
                self.logger.error("Attributes missing for class, video was not compiled.")


    def record_screen(self):
        """
            Begins screen recording, utilises attributes set within the class on initialisation.
            @params:
                None
        """
        if self.driver is not None:
            self.logger.info("Starting recording process...")
            self.imgs = []
            recorder_thread = threading.Thread(target=self.__record_function, name="Screen Recorder", args=[self.imgs])
            recorder_thread.start()

    @staticmethod
    def get_opencv_img_from_bytes(byte_string, flags=None):
        """
            Converts bytes to OpenCV Img object
            @params:
                byte_string    - Required  : Bytes object representing image data. (bytes)
                flags          - Optional  : Specifies cv2 flag for image (cv2 Flag)
            @returns:
                OpenCV img
        """
        if flags in [None, False]:
            try:
                flags = cv2.IMREAD_COLOR
            except Exception:
                return False
        bytes_as_np_array = np.fromstring(byte_string, np.uint8)
        return cv2.imdecode(bytes_as_np_array, flags)

    def __generate_file_and_temp_location(self):
        """
            Generate correct file location and folder location for temporary files
            @params:
                None
            @returns:
                tuple containing file location and folder location for temporary files respectively.
        """
        temp_location = "temp_images"
        current_file = self.file_name
        if not current_file.lower().endswith(self.video_format):
            current_file = (f"{current_file}.{self.video_format}")
        if self.file_path_root is not None:
            if self.file_path_root.exists():
                current_file = str(self.file_path_root / current_file)
                temp_location = str(self.file_path_root / "temp_images")
        return current_file, temp_location

    def __record_function(self, imgs):
        """
            Private method triggered within an individual thread to handle screen recording seperately.
            @params:
                imgs    - Required  : List acting as a container for byte strings representing screenshots (List)
            @returns:
                List of generated imgs
        """
        # ignore blank frames on startup before window is loaded
        while not self.driver.current_url or self.driver.current_url == "data:,":
            pass
        self.record = True
        while self.record:
            img = None
            if self.driver:
                try:
                    img = self.driver.get_screenshot_as_png()
                except Exception:
                    pass
            else:
                try:
                    img = pyautogui.screenshot()
                except Exception:
                    pass
            if img is not None:
                imgs.append(img)
        self.logger.info("Stopping recording...")
        return imgs


    def imgs_to_file_list(self, imgs, temp_location):
        """
            Converts list of OpenCV Imgs to rendered images at a location
            @params:
                imgs             - Required  : List of Bytes objects representing image data. (List)
                temp_location    - Required  : Filepath for rendered images (String)
            @returns:
            Tuple of 3 values - list of rendered image filepaths, height of image, width of image
        """
        width = False
        height = False
        files = []
        for idx, img in enumerate(imgs):
            img_path = self.create_image_from_bytes(img, temp_location, idx)
            img_obj = cv2.imread(img_path)
            files.append(img_obj)
            if height is False and width is False:
                height, width, _ = img_obj.shape
        return files, height, width

    @staticmethod
    def convert_to_img(data_input):
        """
            Converts strings and bytes to OpenCV Imgs
            @params:
                data_input       - Required  : String representing file_path of an image, or Bytes representing Image data. (String/Bytes)
            @returns:
                cv2 Image if String as input, numpy array if bytes as input, or raw input returned if input is not str or bytes
        """
        if isinstance(input, str):
            try:
                return cv2.imread(data_input)
            except Exception:
                pass
        if isinstance(data_input, bytes):
            try:
                return np.frombuffer(data_input, dtype=np.uint8)
            except Exception:
                pass
        else:
            return data_input

    def create_image_from_bytes(self, bytes_obj, root, file_name, extension="png"):
        """
            Converts bytes to image file on disk
            @params:
                bytes_obj  - Required  : Bytes representing Image data. (Bytes)
                root       - Required  : Root of file path. (String)
                file_name  - Required  : Name of output file. (String)
                extension  - Optional  : String representing video format output - mp4/avi (String)
            @return:
                String of file path of new Image
        """
        img_path = f"{root}\\{file_name}.{extension}"
        with open(img_path, "wb") as f:
            f.write(bytes_obj)
        return img_path

    def write_file_list_to_video_file(self, files, height=None, width=None, output_file=None, overwrite=True,
                                      temp_location=None):
        """
            Writes a list of images that exist on disk to video file.
            @params:
                files         - Required  : Bytes representing Image data. (List)
                height        - Optional  : Int representing height of video. (int)
                width         - Optional  : Int representing width of video. (int)
                output_file   - Optional  : String representing filename of output - mp4/avi (String)
                overwrite     - Optional  : Boolean determining whether an existing file of the same name should be overwritten (Boolean)
                temp_location - Optional  : String representing location of temporary files - mp4/avi (String)
            @return:
                None
        """
        self.logger.info("Compiling screen recording.")
        if height is None or width is None:
            try:
                width, height = self.convert_to_img(files[0]).size
            except Exception:
                try:
                    width, height = Image.open(BytesIO(files[0])).size
                except Exception:
                    self.logger.error("Could not determine video resolution, exiting function...")
                    return None
        video_format = self.video_format
        if video_format.lower() == "mp4":
            video_format += "v"
        elif video_format.lower() == "avi":
            video_format = "divx"
        if os.path.exists(output_file):
            if overwrite:
                self.logger.info(f"File '{output_file}' already exists, and will be overwritten.")
            else:
                self.logger.info(f"File '{output_file}' already exists, and will NOT be overwritten, exiting function.")
                return None

        start = default_timer()
        out = cv2.VideoWriter(output_file, cv2.VideoWriter_fourcc(*video_format.lower()), self.fps, (width, height))
        for idx,file in enumerate(self.progress_bar(files, prefix="Progress:", suffix="Complete", length=50)):
            try:
                try:
                    if temp_location:
                        img_path = self.create_image_from_bytes(file, temp_location, idx)
                        img_obj = cv2.imread(img_path)
                        out.write(img_obj)
                except Exception:
                    img = self.convert_to_img(file)
                    out.write(img)
            except Exception:
                pass
            time.sleep(0.1)
        out.release()
        cv2.destroyAllWindows()
        end = default_timer()
        self.logger.success(f"Video compilation complete - Duration: {str(timedelta(seconds=end - start))}")

    def img_path_list_to_cv2_img_list(self, imgs):
        """
            Converts list of rendered images on disk to list of OpenCV images at a location
            @params:
                imgs             - Required  : List of Bytes objects representing image data. (List)
            @return:
                List of OpenCV images
        """
        res = []
        for img_path in imgs:
            res.append(cv2.imread(img_path))
        return res

    def create_video_from_img_folder(self, img_folder, output_file, temp_location=None):
        """
            Converts folder of imgs to video
            @params:
                img_folder       - Required  : Filepath containing images to be rendered to video. (String)
                output_file      - Required  : Filepath for output file (String)
                temp_location    - Optional  : Filepath for temporary files (String)
            @returns:
                None
        """
        list_of_files = list(filter(os.path.isfile, glob.glob(img_folder + '*.png')))
        list_of_files.sort(key=lambda f: int(re.sub('\D', '', f)))
        if list_of_files:
            im = Image.open(list_of_files[0])
            width, height = im.size
            self.write_file_list_to_video_file(list_of_files, height, width, output_file, temp_location)
            self.validate_video_creation(output_file, temp_location)

    def validate_video_creation(self, output_file, temp_location=None):
        """
            Validates video was created and is populated, can optionally delete the folder of temporary data.
            @params:
                output_file      - Required  : Filepath containing rendered video. (String)
                temp_location    - Optional  : Filepath for temporary files (String)
            @return:
                None
        """
        if not os.path.exists(output_file):
            self.logger.error(f"File '{output_file}' was NOT created.")
        elif os.stat(output_file).st_size == 0:
            self.logger.warning(f"File '{output_file}' was created but is EMPTY.")
        else:
            self.logger.success(f"File '{output_file}' has been created and populated.")
            if temp_location is not None:
                self.logger.info(f"Removing temporary images at '{temp_location}'.")
                try:
                    shutil.rmtree(temp_location, ignore_errors=True)
                except Exception as e:
                    self.logger.warning(f"There was an issue deleting the folder '{temp_location}' - {str(e)}")

    # Credit for this method goes to user Greenstick from this StackOverflow post answer -
    # https://stackoverflow.com/questions/3173320/text-progress-bar-in-terminal-with-block-characters
    def progress_bar(self, iterable, prefix='', suffix='', decimals=1, length=100, fill='█', print_end=''):
        """
        Call in a loop to create terminal progress bar
        @params:
            iterable    - Required  : iterable object (Iterable)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
            printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
        @return:
            None
        """
        total = len(iterable)

        # Progress Bar Printing Function
        def print_progress_bar(iteration):
            percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
            filled_length = int(length * iteration // total)
            bar = fill * filled_length + '-' * (length - filled_length)
            print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=print_end)

        # Initial Call
        print_progress_bar(0)
        # Update Progress Bar
        for i, item in enumerate(iterable):
            yield item
            print_progress_bar(i + 1)
        # Print New Line on Complete
        print()