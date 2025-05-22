@echo off
REM Build exe từ spec
rmdir /s /q build
rmdir /s /q dist
python -m PyInstaller Testing_tool.spec

REM Nén folder dist\Testing_tool thành file .zip (yêu cầu đã cài 7-Zip và thêm vào PATH)
if exist dist\Testing_tool (
    if exist Testing_tool.zip del Testing_tool.zip
    7z a -tzip Testing_tool.zip .\dist\Testing_tool\*
) else (
    echo Folder dist\Testing_tool không tồn tại!
    exit /b 1
)

REM Move file .zip sang Release_update, ghi đè nếu đã có
if not exist Release_update mkdir Release_update
move /Y Testing_tool.zip Release_update\Testing_tool.zip

echo Done!
pause