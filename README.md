# ScreenRecorder
A class that allows screen recording of Selenium in Python.

Sometimes debugging an issue using only screenshots can be difficult.
While there are powerful libraries like ffmpeg for video recording, what if you are running a scheduled Selenium test on a remote desktop headlessly?
From my experience, headless execution is difficult to record.
This is a rudimentary library to help with debugging, and will not return the steadiest video stream, but it will return a functional one.

It works by polling screenshots from the Selenium WebDriver in the background in its own thread, returning them as bytes.
When the recording is halted, the bytes are written to a temporary location on disk as images, and then fed into a VideoWriter object, with the temporary images deleted thereafter.

###
Note

Specifying frames per second is not feasible for now, as you would have to poll for a screenshot every (60/n) seconds (where is n is the specified frames per second),
which is too intensive with this model.
