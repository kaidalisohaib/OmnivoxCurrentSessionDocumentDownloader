## Steps to run the script

##### Steps to setup the environment (1 and 2)

1. Run this command to create a virtual environment

    ```Batchfile
    python -m venv venv
    ```

2. Run this command to activate the virtual environment on windows

    ```Batchfile
    .\venv\Scripts\activate.bat
    ```

3. Run the command below to download the required python packages to run the script

    ```Batchfile
    pip install -r requirements.txt
    ```

4. Run this command to start the script

    ```Batchfile
    python main.py
    ```

## Convert the script to a single .exe file

```Batchfile
pyinstaller --onefile main.py
```

The exe file should be located in generated folder "dist".
