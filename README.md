# btReload is a python tool to monitor and del bitcomit task file for testing 
  
# requirement
  1. python 3.5
  2. PyQt
  3. lxml
  4. bitcomit (1.45) with remote web enable

# install
  1. install python-3.5.4.exe or python-3.5.4-amd64.exe (add python to system's ''PATH)
  2. install sip (in cmd window, require by PyQt5)
```
  pip install sip
```
  
  3. install PyQt5 (in cmd window)
```
  pip install PyQt5
```
  
  4. install lxml (in cmd window)
```
  pip install lxml
```

# TODO:
  1. read current upload/download speed
  2. start/stop all button

# NOTE:
  Window 7/8/8.1 require to install kb2999226 to fix the "The procress entry point ucrtbase.terminate could not be locate in the dynamic link library api-ms-win-crt-runtime-l1-1-0.dll" problem when package into an exe file. 
