import requests
import os
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
import os
from requests.adapters import TimeoutSauce


class CustomTimeout(TimeoutSauce):
    def __init__(self, *args, **kwargs):
        if kwargs["connect"] is None:
            kwargs["connect"] = REQUESTS_TIMEOUT_SECONDS
        if kwargs["read"] is None:
            kwargs["read"] = REQUESTS_TIMEOUT_SECONDS
        super().__init__(*args, **kwargs)


default_timeout = 5
current_time_out = default_timeout
REQUESTS_TIMEOUT_SECONDS = float(os.getenv("REQUESTS_TIMEOUT_SECONDS", default_timeout))
requests.adapters.TimeoutSauce = CustomTimeout
path = f"NONE"
url = f"NONE"
all_content = "NONE"
all_file = list()
fail_log = list()


def show_main_menu():
    print("Please select one command from this list.\n"
          f"1) Set path. ({path})\n"
          f"2) Set URL. ({url})\n"
          "3) View all downloadable files.\n"
          "4) Download.\n"
          f"5) Set timeout. ({current_time_out})\n"
          "6) Redownload failed files.\n"
          "7) Exit.")


def set_timeout():
    global REQUESTS_TIMEOUT_SECONDS
    global current_time_out
    global default_timeout
    try:
        current_time_out = float(input("Please input how long timeout is : "))
        print("Timeout's set.")
    except ValueError:
        current_time_out = default_timeout
        print("Error. Set to default. Returning to main menu...")
    REQUESTS_TIMEOUT_SECONDS = float(os.getenv("REQUESTS_TIMEOUT_SECONDS", current_time_out))


def reset_timeout():
    global REQUESTS_TIMEOUT_SECONDS
    global current_time_out
    REQUESTS_TIMEOUT_SECONDS = float(os.getenv("REQUESTS_TIMEOUT_SECONDS", current_time_out))


def set_path():
    global path
    p = input("Please type in a path : ").strip()
    try:
        if os.path.exists(p):
            path = p
        print("Path's set.")
    except FileNotFoundError:
        print("Directory error. Returning to main menu...")


def set_link():
    global url
    global all_content
    global all_file
    l = input("Please type in a URL : ").strip()
    try:
        requests.get(l)  # Testing URL
        url = l
        r = requests.get(url)
        all_content = BeautifulSoup(r.content, "html.parser")
        all_file = all_content.find_all('a')
        print("URL's set.")
    except requests.exceptions.MissingSchema or requests.exceptions.InvalidURL:
        print("Invalid URL. Returning to main menu...")
    except requests.exceptions:
        print("Error happened. Please try again later. Returning to main menu....")


def show_all_downloadable():
    global all_file
    i = 1
    print("List")
    for file in all_file:
        print(f"{i}) {file.get('href')}")
        i += 1


def select_which_to_download():
    global all_file
    n = set()
    a = input(f"Which file you want to download [example : 33,2-9,all (all is equal to 1-{len(all_file)})]:\n")
    for inp in a.split(","):
        try:
            if inp == "all":
                for k in range(0, len(all_file)):
                    n.add(k)
                break
            elif inp.find("-") != -1:
                i = int(inp.split("-")[0]) - 1
                j = int(inp.split("-")[1]) - 1
                for k in range(i, j+1):
                    n.add(k)
            else:
                i = int(inp) - 1
                n.add(i)
        except ValueError:
            print("Error: Please input integer. Returning to main menu...")
            return
    n = sorted(list(n))
    download_all_file(n)


def download_all_file(n):
    global all_file
    global fail_log

    fail_log.clear()
    sess = requests.session()
    adap = HTTPAdapter(max_retries=5, pool_connections=1)
    sess.mount('https://', adap)

    current_file_done = 0
    file_amount = len(n)

    for selected in n:
        link = all_file[selected].get('href')
        print(link)
        print(f"file {selected + 1}")
        if str(link).startswith('..'):
            continue
        try:
            res = download_file(url + link, sess, f'({selected + 1}) ', '')
        except Exception as ex:
            res = None
        if res:
            current_file_done += 1
            print(f'download complete {current_file_done}/{file_amount}')
        else:
            print(f'download failed {link}')
            fail_log.append(selected)
        print(f"----------------------------------------------------------------")
    print(f'\nDownloads finished!!')
    print(f'Amount of completed download : {current_file_done}/{file_amount}')
    print(f'Amount of failed download : {file_amount - current_file_done}/{file_amount}')
    print(f"Index of failed download : {' '.join([str(i + 1) for i in fail_log])}")
    sess.close()


def download_file(url_to_download: str, session, prefix, suffix):
    print("downloading " + url_to_download + "...")
    try:
        content_from_this_link = session.get(url_to_download)
    except requests.exceptions.ConnectionError:
        print("Timeout happens.")
        reset_timeout()
        return False
    print(f"status code: {content_from_this_link.status_code}")
    if content_from_this_link.status_code == 200:
        file_name = str(url_to_download).strip().split("/")[-1]
        open(path + prefix + file_name + suffix, "wb").write(content_from_this_link.content)
        return True
    else:
        return False


def redownload_failed_file():
    global fail_log
    g = [i for i in fail_log]
    download_all_file(g)


if __name__ == "__main__":
    print("Welcome to MassFileDownloader!\n")
    while True:
        show_main_menu()
        try:
            i = int(input("Selected command : "))
        except ValueError:
            i = -1
        print()
        if i == 1:
            set_path()
        elif i == 2:
            set_link()
        elif i == 3:
            if url == "NONE":
                print("Please set the URL first.")
            else:
                show_all_downloadable()
        elif i == 4:
            if url == "NONE" or path == "NONE":
                print("Please setup everything first.")
            elif len(all_file) == 0:
                print("There is no file to download.")
            else:
                select_which_to_download()
        elif i == 5:
            set_timeout()
        elif i == 6:
            if len(fail_log) == 0:
                print("There is no failed file yet.")
            else:
                redownload_failed_file()
        elif i == 7:
            break
        else:
            print("This command is invalid.")
        print("----------------------------------------------------------------")
