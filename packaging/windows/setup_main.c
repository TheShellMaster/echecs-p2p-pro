
#include <windows.h>
#include <shlobj.h>
#include <stdio.h>
#include <stdlib.h>

#define IDR_PAYLOAD 101

void CreateShortcut(LPCSTR targetPath, LPCSTR shortcutPath, LPCSTR iconPath) {
    char cmd[1024];
    sprintf(cmd, "powershell -Command \"$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%s'); $s.TargetPath = '%s'; $s.IconLocation = '%s,0'; $s.Save()\"",
            shortcutPath, targetPath, iconPath);
    system(cmd);
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    int res = MessageBoxA(NULL,
        "Bienvenue dans l'assistant d'installation d'Échecs P2P Pro v2.1.0 !\n\n"
        "Voulez-vous installer le jeu avec raccourcis Bureau et Menu Démarrer ?",
        "Installation — Échecs P2P Pro",
        MB_YESNO | MB_ICONQUESTION);

    if (res != IDYES) {
        return 0;
    }

    // Récupération de LOCALAPPDATA
    char appData[MAX_PATH];
    if (FAILED(SHGetFolderPathA(NULL, CSIDL_LOCAL_APPDATA, NULL, 0, appData))) {
        strcpy(appData, "C:\\");
    }

    char installDir[MAX_PATH];
    sprintf(installDir, "%s\\Programs\\EchecsP2P", appData);
    CreateDirectoryA(installDir, NULL);

    char zipPath[MAX_PATH];
    sprintf(zipPath, "%s\\setup_temp.zip", installDir);

    // Extraction de la ressource payload zip
    HRSRC hRes = FindResourceA(hInstance, MAKEINTRESOURCEA(IDR_PAYLOAD), RT_RCDATA);
    if (!hRes) {
        // Fallback recherche première ressource RCDATA
        hRes = FindResourceA(hInstance, "IDR_PAYLOAD", RT_RCDATA);
    }

    if (hRes) {
        HGLOBAL hGlob = LoadResource(hInstance, hRes);
        DWORD size = SizeofResource(hInstance, hRes);
        LPVOID data = LockResource(hGlob);
        if (data && size > 0) {
            FILE *fp = fopen(zipPath, "wb");
            if (fp) {
                fwrite(data, 1, size, fp);
                fclose(fp);

                // Décompression PowerShell
                char unzipCmd[1024];
                sprintf(unzipCmd, "powershell -Command \"Expand-Archive -Path '%s' -DestinationPath '%s' -Force\"", zipPath, installDir);
                system(unzipCmd);
                DeleteFileA(zipPath);
            }
        }
    }

    // Création des raccourcis Bureau et Menu
    char exePath[MAX_PATH];
    char iconPath[MAX_PATH];
    sprintf(exePath, "%s\\EchecsP2P.exe", installDir);
    sprintf(iconPath, "%s\\assets\\icon.ico", installDir);

    char desktopPath[MAX_PATH];
    if (SUCCEEDED(SHGetFolderPathA(NULL, CSIDL_DESKTOPDIRECTORY, NULL, 0, desktopPath))) {
        char linkPath[MAX_PATH];
        sprintf(linkPath, "%s\\Échecs P2P Pro.lnk", desktopPath);
        CreateShortcut(exePath, linkPath, iconPath);
    }

    char startMenuPath[MAX_PATH];
    if (SUCCEEDED(SHGetFolderPathA(NULL, CSIDL_PROGRAMS, NULL, 0, startMenuPath))) {
        char linkPath[MAX_PATH];
        sprintf(linkPath, "%s\\Échecs P2P Pro.lnk", startMenuPath);
        CreateShortcut(exePath, linkPath, iconPath);
    }

    // Inscription dans la base de registre (Désinstallation)
    HKEY hKey;
    if (RegCreateKeyA(HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\EchecsP2P", &hKey) == ERROR_SUCCESS) {
        const char *dispName = "Échecs P2P Pro (v2.1.0)";
        const char *version = "2.1.0";
        RegSetValueExA(hKey, "DisplayName", 0, REG_SZ, (const BYTE*)dispName, strlen(dispName)+1);
        RegSetValueExA(hKey, "DisplayVersion", 0, REG_SZ, (const BYTE*)version, strlen(version)+1);
        RegSetValueExA(hKey, "DisplayIcon", 0, REG_SZ, (const BYTE*)iconPath, strlen(iconPath)+1);
        RegSetValueExA(hKey, "InstallLocation", 0, REG_SZ, (const BYTE*)installDir, strlen(installDir)+1);
        RegCloseKey(hKey);
    }

    int launch = MessageBoxA(NULL,
        "Installation terminée avec succès !\n\n"
        "Un raccourci a été ajouté sur votre Bureau.\n"
        "Voulez-vous lancer Échecs P2P Pro maintenant ?",
        "Installation Terminée",
        MB_YESNO | MB_ICONINFORMATION);

    if (launch == IDYES) {
        ShellExecuteA(NULL, "open", exePath, NULL, installDir, SW_SHOWNORMAL);
    }

    return 0;
}
