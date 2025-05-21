@echo off
@REM REM Build exe từ spec
@REM python -m PyInstaller Testing_tool.spec

REM Nén folder dist\Testing_tool thành file .7z (yêu cầu đã cài 7-Zip và thêm vào PATH)
if exist dist\Testing_tool (
    if exist Testing_tool.7z del Testing_tool.7z
    7z a -t7z Testing_tool.7z .\dist\Testing_tool\*
) else (
    echo Folder dist\Testing_tool không tồn tại!
    exit /b 1
)

REM Move file .7z sang Release_update, ghi đè nếu đã có
if not exist Release_update mkdir Release_update
move /Y Testing_tool.7z Release_update\Testing_tool.7z

echo Done!
pause