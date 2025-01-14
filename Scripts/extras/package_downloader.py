#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
# 
# SPDX-License-Identifier: Apache-2.0 OR MIT
#
#

import os
import urllib
import urllib.request
from urllib.error import URLError
import ssl
import certifi
import hashlib
import pathlib
import tarfile
import sys


# used if LY_PACKAGE_SERVER_URLS is not set.
DEFAULT_LY_PACKAGE_SERVER_URLS = "https://d2c171ws20a1rv.cloudfront.net"

# its not necessarily the case that you ever actually have to use boto3
# if all the servers you specify in your server list (Default above) are 
# not s3 buckets.  So it is not a failure to be missing boto3 unless you actually
# try to use it later.
_aws_s3_available = False
try:
    import boto3
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
    _aws_s3_available = True
except:
    pass

class PackageDownloader(): 
    @staticmethod
    def DownloadAndUnpackPackage(package_name, package_hash, folder_target):
        '''Given a package name, hash, and folder to unzip it into, 
            attempts to find the package. If found, downloads and unpacks to the target_folder location.
            Only the first found package is downloaded, and then the search stops. If the checksum of
            the downloaded file doesn't match the checksum in the O3DE dependency list, the package
            isn't unpacked on the filesystem and the download is deleted.
        
            This method supports all URI types handled by the O3DE package system, including S3 URIs.
            
            PRECONDITIONS:
            * LY_PACKAGE_SERVER_URLS must be set in the environment to override the defaultg
            * If using S3 URIs, LY_AWS_PROFILE must be set in the environment and the 'aws' command
              must be on the PATH
            
            Returns True if successful, False otherwise.
         '''

        def ComputeHashOfFile(file_path):
            file_path = os.path.normpath(file_path)
            hasher = hashlib.sha256()
            hash_result = None
            
            # we don't follow symlinks here, this is strictly to check actual packages.
            with open(file_path, 'rb') as afile:
                buf = afile.read()
                hasher.update(buf)
                hash_result = hasher.hexdigest()
        
            return hash_result

        # make sure a package with that name is not already present:
        server_urls = os.environ.get("LY_PACKAGE_SERVER_URLS", default = "")

        if not server_urls:
            print(f"Server url list is empty - please set LY_PACKAGE_SERVER_URLS env var to semicolon-seperated list of urls to check")
            print(f"Using default URL for convenience: {DEFAULT_LY_PACKAGE_SERVER_URLS}")
            server_urls = DEFAULT_LY_PACKAGE_SERVER_URLS

        download_location = pathlib.Path(folder_target)
        package_file_name = package_name + ".tar.xz"
        package_download_name = download_location / package_file_name
        package_unpack_folder = download_location / package_name
        
        server_list = server_urls.split(';')

        try:
            package_download_name.unlink()
        except FileNotFoundError:
            pass
        download_location.mkdir(parents=True, exist_ok=True)

        print(f"Downloading package {package_name}...")

        for package_server in server_list:
            if not package_server:
                continue
            full_package_url = package_server + "/" + package_file_name
            print(f"    - attempting '{full_package_url}' ...")

            try:
                if full_package_url.startswith("s3://"):
                    if not _aws_s3_available:
                        print(f"S3 URL given, but boto3 could not be located. Please ensure that you have installed")
                        print(f"installed requirements: {sys.executable} -m pip install --upgrade boto3 certifi six")
                        continue
                    # it may be legitimate not have a blank AWS profile, so we can't supply a default here
                    aws_profile_name = os.environ.get("LY_AWS_PROFILE", default = "")
                    # if it is blank, its still worth noting in the log:
                    if not aws_profile_name:
                        print("    - LY_AWS_PROFILE env var is not set - using blank AWS profile by default")
                    session = boto3.session.Session(profile_name=aws_profile_name)
                    bucket_name = full_package_url[len("s3://"):]
                    slash_pos = bucket_name.find('/')
                    if slash_pos != -1:
                        bucket_name = bucket_name[:slash_pos]
                    print(f"    - using aws to download {package_file_name} from bucket {bucket_name}...")
                    session.client('s3').download_file(bucket_name, package_file_name, str(package_download_name))
                else:
                    tls_context = ssl.create_default_context(cafile=certifi.where())
                    with urllib.request.urlopen(url=full_package_url, context = tls_context) as server_response:
                        print("    - Downloading package...")
                        file_data = server_response.read()
                        with open(package_download_name, "wb") as save_package:
                            save_package.write(file_data)
            except (ClientError, BotoCoreError, ssl.SSLError, URLError, OSError) as e:
                print(f"        - Unable to get package from this server: {e}")
                continue # try the next URL, if any...

            try:
                # validate that the package matches its hash
                print("    - Checking hash ... ")
                hash_result = ComputeHashOfFile(str(package_download_name))
                if hash_result != package_hash:
                    print("    - Warning: Hash of package does not match - will not use it")
                    continue

                # hash matched.  Unpack and return!
                package_unpack_folder.mkdir(parents=True, exist_ok=True)
                with tarfile.open(package_download_name) as archive_file:
                    print("    - unpacking package...")
                    archive_file.extractall(package_unpack_folder)
                    print(f"Downloaded successfuly to {os.path.realpath(package_unpack_folder)}")
                return True
            except (OSError, tarfile.TarError) as e:
                # note that anything that causes this to fail should result in trying the next one.
                print(f"    - unable to unpack or verify the package: {e}")
                continue # try the next server, if you have any
            finally:
                # clean up
                if os.path.exists(package_download_name):
                    try:
                        os.remove(package_download_name)
                    except:
                        pass
        print("FAILED - unable to find the package on any servers.")
        return False

# you can also use this module from a bash script to get a package
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Download, verify hash, and unpack a 3p package")

    parser.add_argument('--package-name',
                        help='The package name to download',
                        required=True)

    parser.add_argument('--package-hash',
                        help='The package hash to verify',
                        required=True)
    
    parser.add_argument('--output-folder',
                        help='The folder to unpack to.  It will get unpacked into (package-name) subfolder!',
                        required=True)

    parsed_args = parser.parse_args()
    if PackageDownloader.DownloadAndUnpackPackage(parsed_args.package_name, parsed_args.package_hash, parsed_args.output_folder):
        sys.exit(0)

    sys.exit(1)

