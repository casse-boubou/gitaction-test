# ENTER ONE LINE DESCRIPTION HERE
import sys
import os


from scripts.manager_process import compare_all_packages, download_all_depot
from scripts.extract_datas import extract_data
from scripts.parser import parser

if __name__ == "__main__":

    dockerfile = sys.argv[1]
    filePath = os.path.join(os.environ["GITHUB_WORKSPACE"],dockerfile)
    # filePath = sys.argv[1] if len(sys.argv) > 1 else "Dockerfile"

    # Parse Dockerfile for extract data
    commandsliste = parser(filePath).cmdlist

    # Check and extract if pinned package is present in Dockerfile
    data = extract_data(commandsliste)
    # print (f"DATA {data}")
    # {'apk': [
    #     ['alpine', '3.24', {'cargo': '1.96.1-r0', 'git': '2.54.0-r0'}, 'RUN', 6],
    #     ['alpine', '3.23', {'cargo': '1.96.1-r0', 'git': '2.54.0-r0'}, 'RUN', 12],
    #     ['alpine', '3.22', {'cargo': '1.96.1-r0', 'git': '2.54.0-r0'}, 'RUN', 34]
    #     ]}

    # Download a fresh version of depot for each version of distribution
    download_all_depot(data)

    # Compare version for each packages
    out_pack = compare_all_packages(data)
    # print(out_pack)
    # {6: {}, 12: {'cargo': ['1.96.1-r0', '1.91.1-r2'], 'git': ['2.54.0-r0', '2.52.0-r0']}, 34: {'cargo': ['1.96.1-r0', '1.87.0-r1'], 'git': ['2.54.0-r0', '2.49.1-r0']}}
    show_warning = True
    for startline, paca in out_pack.items():
        if paca and show_warning:
            print("WARNING !! some packages appear to be out of date. This could block the build of docker image")
            print("Check the corresponding versions for the following packages:")
            show_warning = False
        if paca:
            for pa, vers in paca.items():
                print(f"Stage start at line {startline}, {pa}: {vers[0]} -> {vers[1]}")
                # continue
    if show_warning is False:
        sys.exit(1)


    print("0")
