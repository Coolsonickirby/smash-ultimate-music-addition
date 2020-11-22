# Smash Ultimate Music Addition Script

## Tools used
- prc2josn: [BenHall-7](https://github.com/BenHall-7/)
- XMSBT_cli: [IcySon55](https://github.com/IcySon55/) & [exelix11](https://github.com/exelix11/)
- smash-bgm-property: [jam1garner](https://github.com/jam1garner/)
- ParamLabels.csv: [BenHall-7](https://github.com/BenHall-7), [jam1garner](https://github.com/jam1garner), [Dr-HyperCake](https://github.com/Dr-HyperCake), [Birdwards](https://github.com/Birdwards), [ThatNintendoNerd](https://github.com/ThatNintendoNerd), [ScanMountGoat](https://github.com/ScanMountGoat), [Meshima](https://github.com/Meshima), [TheSmartKid](https://github.com/TheSmartKid), & [Blazingflare](https://github.com/Blazingflare)

## How to use
1. Make sure you place all the nessecary files in the `files` folder
2. Make sure you have the latest version of Python installed and added to PATH
3. Run `pip -r requirements.txt` with the Command Prompt in the current directory as the project
4. Put your `nus3audio` files in the `music` folder (You can create more folders inside `music` for organizations sake)
5. Create a `config.toml` file for your music in the `music` folder (there can be multiple config files in folders too)
6. Run `python add_songs.py` in the Command Prompt and follow the on-screen instructions
7. (If FTP is turned off) Copy everything in the output folder to `sd:/ultimate/mods/[Mod Folder Name]/`