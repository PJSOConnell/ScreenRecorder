import os
import time
import re
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


class ScreenRecord:
    def __init__(self, **kwargs):
        #Driver required to take screenshots, video_format optional and can be arrived from file_name.
        #file_name can be a full path.
        self.driver = kwargs["driver"]
        self.file_name = kwargs.get("file_name")
        self.video_format = kwargs.get("video_format", None)
        if self.video_format is None:
            if self.file_name:
                self.video_format = self.file_name[self.file_name.rindex(".")+1:]
        elif self.video_format.startswith("."):
            self.video_format = self.video_format[1:]
        self.fps = int(kwargs.get("fps", 4))
        self.record = False

    def stop_recording(self, cleanup=True):
        if self.record:
            self.record = False
            if cleanup:
                current_file, temp_location = self.generate_file_and_temp_location()
                if hasattr(self, "imgs"):
                    if self.imgs:
                        if not os.path.exists(temp_location):
                            os.makedirs(temp_location)
                        self.write_file_list_to_video_file(self.imgs, output_file=current_file,
                                                           temp_location=temp_location)
                        self.validate_video_creation(current_file, temp_location)
                        delattr(self, "imgs")
            else:
                print("Attributes missing for class, video was not compiled.")

    def record_screen(self):
        if self.driver is not None:
            self.imgs = []
            recorder_thread = threading.Thread(target=self.record_function, name="Screen Recorder", args=[self.imgs])
            recorder_thread.start()

    @staticmethod
    def get_opencv_img_from_bytes(byte_string, flags=None):
        if flags in [None, False]:
            try:
                flags = cv2.IMREAD_COLOR
            except Exception:
                return False
        bytes_as_np_array = np.fromstring(byte_string, np.uint8)
        return cv2.imdecode(bytes_as_np_array, flags)

    def generate_file_and_temp_location(self):
        current_file = self.file_name
        temp_location = current_file + "\\temp_images"
        if not current_file.lower().endswith(self.video_format):
            current_file += ("\\screen_recording." + self.video_format)
        return current_file, temp_location

    def record_function(self, imgs):
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
        print("Stopping recording...")
        return imgs

    def imgs_to_file_list(self, imgs, temp_location):
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
        img_path = f"{root}\\{file_name}.{extension}"
        f = open(img_path, "wb")
        f.write(bytes_obj)
        f.close()
        return img_path

    def write_file_list_to_video_file(self, files, height=None, width=None, output_file=None, overwrite=True,
                                      temp_location=None):
        print("Compiling screen recording.")
        if height is None or width is None:
            try:
                width, height = self.convert_to_img(files[0]).size
            except Exception:
                try:
                    width, height = Image.open(BytesIO(files[0])).size
                except Exception:
                    print("Could not determine video resolution, exiting function...")
                    return None
        video_format = output_file[output_file.rindex(".") + 1:]
        if video_format.lower() == "mp4":
            video_format += "v"
        elif video_format.lower() == "avi":
            video_format = "divx"
        if os.path.exists(output_file):
            if overwrite:
                print(f"File '{output_file}' already exists, and will be overwritten.")
            else:
                print(f"File '{output_file}' already exists, and will NOT be overwritten, exiting function.")
                return None

        start = default_timer()
        out = cv2.VideoWriter(output_file, cv2.VideoWriter_fourcc(*video_format.lower()), self.fps, (width, height))
        for idx, file in enumerate(self.progress_bar(files, prefix="Progress:", suffix="Complete", length=50)):
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
        print(f"Video compilation complete - Duration: {str(timedelta(seconds=end - start))}")

    def img_path_list_to_cv2_img_list(self, imgs):
        res = []
        for img_path in imgs:
            res.append(cv2.imread(img_path))
        return res

    def create_video_from_img_folder(self, img_folder, output_file, temp_location=None):
        list_of_files = list(filter(os.path.isfile, glob.glob(img_folder + '*.png')))
        list_of_files.sort(key=lambda f: int(re.sub('\D', '', f)))
        if list_of_files:
            im = Image.open(list_of_files[0])
            width, height = im.size
            self.write_file_list_to_video_file(list_of_files, height, width, output_file, temp_location)
            self.validate_video_creation(output_file, temp_location)

    def validate_video_creation(self, output_file, temp_location=None):
        if not os.path.exists(output_file):
            print(f"File '{output_file}' was NOT created.")
        elif os.stat(output_file).st_size == 0:
            print(f"File '{output_file}' was created but is EMPTY.")
        else:
            print(f"File '{output_file}' has been created and populated.")
            if temp_location is not None:
                print(f"Removing temporary images at '{temp_location}'.")
                try:
                    shutil.rmtree(temp_location, ignore_errors=True)
                except Exception as e:
                    print(f"There was an issue deleting the folder '{temp_location}' - {str(e)}")

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

