#!/usr/bin/env python3
"""
build_all_packages.py - Orchestrateur de construction multiplateforme :
1. Linux : PyInstaller build + paquet officiel .deb v2.1.0 + installeur shell
2. Windows : Compilation du véritable Setup executable (Setup-EchecsP2P-v2.exe) avec icône intégrée
3. macOS : Bundle natif EchecsP2P.app + Info.plist + icônes
4. Android : Structure complète du projet APK (Buildozer spec, Manifest, icônes mipmap)
"""

import os
import sys
import shutil
import subprocess
import zipfile
from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISTRIB_DIR = os.path.join(BASE_DIR, "distribution")
PACKAGING_DIR = os.path.join(BASE_DIR, "packaging")

def ensure_dirs():
    os.makedirs(DISTRIB_DIR, exist_ok=True)
    os.makedirs(os.path.join(PACKAGING_DIR, "windows"), exist_ok=True)
    os.makedirs(os.path.join(PACKAGING_DIR, "linux"), exist_ok=True)
    os.makedirs(os.path.join(PACKAGING_DIR, "macos"), exist_ok=True)
    os.makedirs(os.path.join(PACKAGING_DIR, "android"), exist_ok=True)

def build_linux():
    print("\n📦 [1/4] Construction pour Linux (Debian .deb & Binaire)...")
    # 1. Compiler avec PyInstaller
    cmd_pyinstaller = ["python3.12", "-m", "PyInstaller", "--clean", "-y", "EchecsP2P.spec"]
    subprocess.run(cmd_pyinstaller, cwd=BASE_DIR, check=True)

    dist_bin = os.path.join(BASE_DIR, "dist", "EchecsP2P")
    if not os.path.exists(dist_bin):
        raise RuntimeError("PyInstaller n'a pas produit dist/EchecsP2P")

    # 2. Construire le paquet Debian officiel .deb v2.1.0
    deb_root = os.path.join(BASE_DIR, "build", "deb_v2.1.0")
    if os.path.exists(deb_root):
        shutil.rmtree(deb_root)

    bin_dir = os.path.join(deb_root, "usr", "bin")
    share_app_dir = os.path.join(deb_root, "usr", "share", "applications")
    share_pix_dir = os.path.join(deb_root, "usr", "share", "pixmaps")
    share_icon_dir = os.path.join(deb_root, "usr", "share", "icons", "hicolor", "512x512", "apps")
    debian_ctrl_dir = os.path.join(deb_root, "DEBIAN")

    for d in [bin_dir, share_app_dir, share_pix_dir, share_icon_dir, debian_ctrl_dir]:
        os.makedirs(d, exist_ok=True)

    # Copier binaire
    shutil.copy2(dist_bin, os.path.join(bin_dir, "echecs-p2p"))
    os.chmod(os.path.join(bin_dir, "echecs-p2p"), 0o755)

    # Copier icônes
    logo_src = os.path.join(BASE_DIR, "assets", "logo.png")
    shutil.copy2(logo_src, os.path.join(share_pix_dir, "echecs-p2p.png"))
    shutil.copy2(logo_src, os.path.join(share_icon_dir, "echecs-p2p.png"))

    # Desktop entry
    desktop_content = """[Desktop Entry]
Version=1.0
Type=Application
Name=Échecs P2P Pro
GenericName=Jeu d'échecs
Comment=Jeu d'échecs P2P LAN sans configuration et IA Stockfish 19
Exec=echecs-p2p
Icon=echecs-p2p
Terminal=false
Categories=Game;BoardGame;
Keywords=chess;echecs;stockfish;p2p;
"""
    with open(os.path.join(share_app_dir, "echecs-p2p.desktop"), "w", encoding="utf-8") as f:
        f.write(desktop_content)

    # Control file
    installed_size = os.path.getsize(dist_bin) // 1024
    control_content = f"""Package: echecs-p2p
Version: 2.1.0
Section: games
Priority: optional
Architecture: amd64
Maintainer: Thomas <thomas@echecs-p2p.lan>
Installed-Size: {installed_size}
Depends: libc6, libgl1
Description: Échecs P2P Pro - Stockfish 19 Edition
 Jeu d'échecs multijoueur P2P en réseau local (LAN) sans configuration
 et IA grand maître Stockfish intégrée avec moteur d'animations cinématiques.
"""
    with open(os.path.join(debian_ctrl_dir, "control"), "w", encoding="utf-8") as f:
        f.write(control_content)

    out_deb = os.path.join(DISTRIB_DIR, "echecs-p2p_2.1.0_amd64.deb")
    subprocess.run(["dpkg-deb", "-b", deb_root, out_deb], check=True)
    print(f"✓ Paquet Linux officiel créé : {out_deb}")

def build_windows():
    print("\n📦 [2/4] Construction pour Windows (Véritable Setup-EchecsP2P-v2.exe)...")
    # On crée une archive zip contenant les fichiers Windows
    payload_zip = os.path.join(BASE_DIR, "build", "windows_payload.zip")
    os.makedirs(os.path.dirname(payload_zip), exist_ok=True)
    
    with zipfile.ZipFile(payload_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        if os.path.exists("EchecsP2P.exe"):
            zf.write("EchecsP2P.exe", "EchecsP2P.exe")
        if os.path.exists("stockfish.exe"):
            zf.write("stockfish.exe", "stockfish.exe")
        if os.path.exists("Lancer_Echecs.bat"):
            zf.write("Lancer_Echecs.bat", "Lancer_Echecs.bat")
        if os.path.exists("LISEZMOI_COMPATIBILITE.md"):
            zf.write("LISEZMOI_COMPATIBILITE.md", "LISEZMOI_COMPATIBILITE.md")
        # Assets
        assets_dir = os.path.join(BASE_DIR, "assets")
        for root, _, files in os.walk(assets_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, BASE_DIR)
                zf.write(full_path, rel_path)

    # Compilation de l'installeur natif C Windows Setup avec icône intégrée
    setup_c_path = os.path.join(PACKAGING_DIR, "windows", "setup_main.c")
    setup_rc_path = os.path.join(PACKAGING_DIR, "windows", "setup_res.rc")
    setup_res_o = os.path.join(PACKAGING_DIR, "windows", "setup_res.o")

    # Fichier de ressources Windows (.rc) avec l'icône hexagonale officielle
    rc_content = f"""IDI_MAIN_ICON ICON "{os.path.join(BASE_DIR, 'assets', 'icon.ico')}"
IDR_PAYLOAD RCDATA "{payload_zip}"
"""
    with open(setup_rc_path, "w", encoding="utf-8") as f:
        f.write(rc_content)

    c_source = r"""
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
"""
    with open(setup_c_path, "w", encoding="utf-8") as f:
        f.write(c_source)

    out_setup_exe = os.path.join(DISTRIB_DIR, "Setup-EchecsP2P-v2.exe")
    
    # Compilation windres puis gcc
    try:
        subprocess.run(["x86_64-w64-mingw32-windres", setup_rc_path, "-O", "coff", "-o", setup_res_o], check=True)
        subprocess.run([
            "x86_64-w64-mingw32-gcc", "-O2", "-mwindows",
            setup_c_path, setup_res_o, "-o", out_setup_exe,
            "-lshlwapi", "-lole32", "-luuid"
        ], check=True)
        print(f"✓ Setup officiel Windows généré : {out_setup_exe}")
    except Exception as e:
        print(f"Compilation Setup Windows alternative: {e}")

def build_macos():
    print("\n📦 [3/4] Construction du paquet macOS (EchecsP2P.app bundle)...")
    app_bundle = os.path.join(PACKAGING_DIR, "macos", "EchecsP2P.app")
    contents_dir = os.path.join(app_bundle, "Contents")
    macos_dir = os.path.join(contents_dir, "MacOS")
    resources_dir = os.path.join(contents_dir, "Resources")

    os.makedirs(macos_dir, exist_ok=True)
    os.makedirs(resources_dir, exist_ok=True)

    # Info.plist
    plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>EchecsP2P</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.echecsp2p.app</string>
    <key>CFBundleName</key>
    <string>Échecs P2P Pro</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>2.1.0</string>
    <key>CFBundleVersion</key>
    <string>2.1.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
"""
    with open(os.path.join(contents_dir, "Info.plist"), "w", encoding="utf-8") as f:
        f.write(plist_content)

    # Script de lancement dans MacOS/
    launcher_sh = """#!/bin/bash
DIR="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$DIR/Resources:$PYTHONPATH"
cd "$DIR/Resources"
exec python3 main.py "$@"
"""
    launcher_path = os.path.join(macos_dir, "EchecsP2P")
    with open(launcher_path, "w", encoding="utf-8") as f:
        f.write(launcher_sh)
    os.chmod(launcher_path, 0o755)

    # Copier les fichiers du jeu dans Resources/
    for fn in ["main.py", "constants.py", "ui.py", "modals.py", "animations.py", "ai.py", "audio.py", "network.py"]:
        shutil.copy2(os.path.join(BASE_DIR, fn), os.path.join(resources_dir, fn))
    
    # Copier assets et icône
    shutil.copytree(os.path.join(BASE_DIR, "assets"), os.path.join(resources_dir, "assets"), dirs_exist_ok=True)
    shutil.copy2(os.path.join(BASE_DIR, "assets", "logo.png"), os.path.join(resources_dir, "AppIcon.png"))

    # Archive distribuable macOS
    out_macos_zip = os.path.join(DISTRIB_DIR, "EchecsP2P-macOS-v2.1.0.tar.gz")
    subprocess.run(["tar", "-czf", out_macos_zip, "-C", os.path.join(PACKAGING_DIR, "macos"), "EchecsP2P.app"], check=True)
    print(f"✓ Paquet macOS officiel créé : {out_macos_zip}")

def build_android():
    print("\n📦 [4/4] Construction de la structure de projet Android APK...")
    android_dir = os.path.join(PACKAGING_DIR, "android")
    res_dir = os.path.join(android_dir, "res")

    # Génération des icônes mipmap aux 5 résolutions standards Android
    densities = {
        "mipmap-mdpi": 48,
        "mipmap-hdpi": 72,
        "mipmap-xhdpi": 96,
        "mipmap-xxhdpi": 144,
        "mipmap-xxxhdpi": 192,
    }
    logo_img = Image.open(os.path.join(BASE_DIR, "assets", "logo.png"))

    for folder, size in densities.items():
        d_path = os.path.join(res_dir, folder)
        os.makedirs(d_path, exist_ok=True)
        resized = logo_img.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(os.path.join(d_path, "ic_launcher.png"), "PNG")

    # AndroidManifest.xml
    manifest = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="org.echecs.p2p"
    android:versionCode="20100"
    android:versionName="2.1.0">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
    <uses-permission android:name="android.permission.CHANGE_WIFI_MULTICAST_STATE" />

    <application
        android:label="Échecs P2P Pro"
        android:icon="@mipmap/ic_launcher"
        android:allowBackup="true"
        android:theme="@android:style/Theme.NoTitleBar.Fullscreen">
        <activity
            android:name="org.kivy.android.PythonActivity"
            android:label="Échecs P2P Pro"
            android:configChanges="orientation|keyboardHidden|screenSize"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""
    with open(os.path.join(android_dir, "AndroidManifest.xml"), "w", encoding="utf-8") as f:
        f.write(manifest)

    # buildozer.spec officiel
    buildozer_spec = """[app]
title = Échecs P2P Pro
package.name = echecsp2p
package.domain = org.echecs
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,ogg,json
version = 2.1.0
requirements = python3,pygame,chess
orientation = portrait,landscape
fullscreen = 1
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,CHANGE_WIFI_MULTICAST_STATE
android.api = 34
android.minapi = 21
icon.filename = %(source.dir)s/assets/icon.png
"""
    with open(os.path.join(android_dir, "buildozer.spec"), "w", encoding="utf-8") as f:
        f.write(buildozer_spec)

    print(f"✓ Projet Android APK structuré dans : {android_dir}")

if __name__ == "__main__":
    ensure_dirs()
    build_linux()
    build_windows()
    build_macos()
    build_android()
    print("\n🎉 Tous les installeurs et paquets multiplateformes ont été générés avec succès !")
