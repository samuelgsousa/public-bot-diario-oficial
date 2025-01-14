@echo off
set PYTHON_INSTALLER=python-installer.exe

REM Verifica se o Python está instalado
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo Python não está instalado. Baixando e instalando Python...
    
    REM Baixa o instalador do Python
    powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.9.7/python-3.9.7-amd64.exe', '%cd%\%PYTHON_INSTALLER%')"
    
    REM Executa o instalador silenciosamente
    start /wait "" "%PYTHON_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1
    
    REM Remove o instalador após instalação
    del "%PYTHON_INSTALLER%"
    
    REM Verifica novamente se o Python está disponível
    python --version >nul 2>&1
    IF ERRORLEVEL 1 (
        echo Falha na instalação do Python. Por favor, instale manualmente e execute o script novamente.
        pause
        exit /b
    )
    echo Python instalado com sucesso.
)

REM Nome do ambiente virtual
set VENV_DIR=env

REM Verifica se o ambiente virtual já existe
IF NOT EXIST "%VENV_DIR%\Scripts\activate" (
    echo Criando ambiente virtual...
    python -m venv %VENV_DIR%
    
    echo Instalando pacotes do requirements.txt...
    call "%VENV_DIR%\Scripts\activate"
    pip install -r requirements.txt
) ELSE (
    echo Ambiente virtual já existe. Ativando...
    call "%VENV_DIR%\Scripts\activate"
)

REM Executa o Streamlit
echo Iniciando o Streamlit...
streamlit run app.py