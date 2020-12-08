import threading
import queue
import RunCompression as rc
import PySimpleGUI as sg


def thread(path, svd_radius, fft_keep, gui_queue):
    """
    A worker thread that communicates to the gui using a queue.
    This is used to perform the computation whilst keeping the GUI responsive
    """
    # do compression with params and get info from compression
    text = rc.do_all_compression(path, svd_radius, fft_keep)
    # pass message to queue for gui
    gui_queue.put(str(text))


def main_window():
    # create a queue for receiving messages from other thread
    gui_queue = queue.Queue()
    # create layout of the gui
    layout = [[sg.Text("Choose an option")],
              [sg.Button("Compress Image"), sg.InputText('Image..', key='compress_input'), sg.FileBrowse()],
              [sg.Text("SVD Radius Value"), sg.InputText('100', key="svd_radius")],
              [sg.Text("Fourier Compression Keep Value"), sg.InputText('0.1', key="fft_keep")],
              [sg.Text("Please select the desired compression details.\n\n\n\n\n\n\n\n", key="output_text")],
              [sg.Button("Exit")]]
    window = sg.Window(title="Image Compression and Decompression", layout=layout)
    # loop for using the gui
    while True:
        # read values from window with timeout of 100ms for getting messages from queue
        event, values = window.read(timeout=100)
        # End program if user closes window or presses exit
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        # compress image event
        elif event == "Compress Image":
            # get value of image to compress
            path = window.Element("compress_input").get()
            # get params
            svd_radius = window.Element("svd_radius").get()
            fft_keep = window.Element("fft_keep").get()
            # update text element
            window.Element("output_text").update("Compressing Image...\n\n\n\n\n\n\n\n")
            # attempt to start a thread to run computation
            try:
                threading.Thread(target=thread, args=(path, svd_radius, fft_keep, gui_queue), daemon=True).start()
            except Exception as e:
                print('Error')
        try:
            # try to get message
            message = gui_queue.get_nowait()
        except queue.Empty:  # get_nowait() will get exception when Queue is empty
            message = None  # break from the loop if no more messages are queued up
        # if message received from queue, display the message in the Window
        if message:
            window.Element("output_text").update(message)


if __name__ == "__main__":
    # run the main_window()
    main_window()
