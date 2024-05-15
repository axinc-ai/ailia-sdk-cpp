#### LICENSE downloader ####

import os
import sys
import platform
import re
import datetime
import http.client
import locale

debug_download = False
display_license_warning = True

LICENSE_SERVER = "axip-console.appspot.com"
LICENSE_API = "/license/download/product/AILIA"


def _download_license(lic_path):
    conn = http.client.HTTPSConnection( LICENSE_SERVER )
    conn.request( "GET", LICENSE_API)
    response = conn.getresponse()
    if response.status!=200:
        raise RuntimeError("License file download failed")
    license_file = response.read()
    with open(lic_path, "wb") as f:
        f.write(license_file)


def _check_license(lic_path):
    user_data = ''

    if not os.path.exists(lic_path):
        return f'License file {lic_path} is not found.', user_data

    invalid_format = f'License file {lic_path} has invalid format.'

    with open(lic_path, "r", encoding="utf-8") as f:
        if f.readline() != "--- shalo license file ---\n":
            return invalid_format, user_data
        if f.readline() != "axell:ailia\n":
            return invalid_format, user_data

        dateline = f.readline()
        m = re.match(r'(\d{4})/(\d{2})/(\d{2})', dateline)
        if m == None:
            return invalid_format, user_data

        date = datetime.datetime(year=int(m[1]), month=int(m[2]), day=int(m[3]), hour=23, minute=59, second=59)
        now = datetime.datetime.now()
        if now > date:
            return f'License date of {lic_path} has been expired.', user_data

        user_data = f.readline()

    return None, user_data


def _display_warning():
    global display_license_warning
    if not display_license_warning:
        return
    locales = locale.getdefaultlocale()
    lang = "en"
    for l in locales:
        if "ja" in l:
            lang = "ja"
        if "zh" in l:
            lang = "zh"
    if lang == "ja":
        print("ailiaへようこそ。ailia SDKは商用ライブラリです。特定の条件下では、無償使用いただけますが、原則として有償ソフトウェアです。詳細は https://ailia.ai/license/ を参照してください。")
    elif lang == "zh":
        print("欢迎来到ailia。ailia SDK是商业库。在特定条件下，可以免费使用，但原则上是付费软件。详情请参阅 https://ailia.ai/license/ 。")
    else:
        print("Welcome to ailia! The ailia SDK is a commercial library. Under certain conditions, it can be used free of charge; however, it is principally paid software. For details, please refer to https://ailia.ai/license/ .")
    display_license_warning = False


def check_and_download_license():
    lic_file_usr = None
    lic_file_sys = None

    if sys.platform == "win32":
        lic_file_sys = str(os.path.dirname(os.path.abspath(__file__))) + "/library/windows/x64/AILIA.lic"
    elif sys.platform == "darwin":
        import pwd
        uid = os.getuid()
        if uid == 0:
            lic_file_sys = os.path.join('/Users/Shared/Library/SHALO', 'AILIA.lic')
        if 'SUDO_UID' in os.environ:
            uid = int(os.environ['SUDO_UID'])
        home = pwd.getpwuid(uid).pw_dir
        lic_file_usr = os.path.join(home, "Library", "SHALO", "AILIA.lic")
    else:
        import pwd
        uid = os.getuid()
        if uid == 0:
            lic_file_sys = os.path.join('/usr/local/etc/shalo', 'AILIA.lic')
        if 'SUDO_UID' in os.environ:
            uid = int(os.environ['SUDO_UID'])
        home = pwd.getpwuid(uid).pw_dir
        lic_file_usr = os.path.join(home, ".shalo", "AILIA.lic")

    user_data = ''

    for lic_file in [lic_file_usr, lic_file_sys]:
        if not lic_file:
            continue
        err, user_data = _check_license(lic_file)
        if err != None or debug_download:
            os.makedirs(os.path.dirname(lic_file), exist_ok=True)
            print("Download license file for ailia SDK.")
            _download_license(lic_file)
        err, user_data = _check_license(lic_file)
        if err != None:
            raise RuntimeError(err)

    if "trial version" in user_data:
        _display_warning()

check_and_download_license()
print("Success")
