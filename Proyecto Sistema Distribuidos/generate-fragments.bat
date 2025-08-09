@echo off

mkdir data\node1 2>nul
mkdir data\node2 2>nul

for /l %%i in (1,1,5) do (
    fsutil file createnew data\node1\fragment_%%i.mp4 1048576
)

for /l %%i in (6,1,10) do (
    fsutil file createnew data\node2\fragment_%%i.mp4 1048576
)

echo Fragmentos generados en data\node1 y data\node2