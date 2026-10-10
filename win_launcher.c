#include <windows.h>
#include <stdio.h>
#include <stdlib.h>

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    // 1. Set current directory to executable directory
    char exePath[MAX_PATH];
    if (GetModuleFileNameA(NULL, exePath, MAX_PATH) > 0) {
        char* lastSlash = strrchr(exePath, '\\');
        if (lastSlash) {
            *lastSlash = '\0';
            SetCurrentDirectoryA(exePath);
        }
    }

    // 2. Prepare startup info
    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    ZeroMemory(&pi, sizeof(pi));

    // 3. Try pythonw.exe main.py (silent GUI window)
    char cmd[MAX_PATH * 2];
    snprintf(cmd, sizeof(cmd), "pythonw.exe main.py %s", lpCmdLine ? lpCmdLine : "");
    if (CreateProcessA(NULL, cmd, NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi)) {
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        return 0;
    }

    // 4. Try python.exe main.py
    snprintf(cmd, sizeof(cmd), "python.exe main.py %s", lpCmdLine ? lpCmdLine : "");
    if (CreateProcessA(NULL, cmd, NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi)) {
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        return 0;
    }

    // 5. Try cmd.exe /c Lancer_Echecs.bat
    snprintf(cmd, sizeof(cmd), "cmd.exe /c Lancer_Echecs.bat");
    if (CreateProcessA(NULL, cmd, NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi)) {
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        return 0;
    }

    // 6. User feedback if python not found
    MessageBoxA(NULL, 
        "Bienvenue sur Echecs P2P Pro (Stockfish 19) !\n\n"
        "Pour lancer le jeu, double-cliquez sur 'Lancer_Echecs.bat' ou installez Python 3.\n\n"
        "Site officiel : https://www.python.org", 
        "Echecs P2P Pro", 
        MB_OK | MB_ICONINFORMATION);
    return 1;
}
