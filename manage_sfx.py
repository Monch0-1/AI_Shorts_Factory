import argparse
from CreateShorts.Services.SFXLibraryManager import SFXLibraryManager

def main():
    parser = argparse.ArgumentParser(description="Unified SFX Library Management Tool")
    parser.add_argument("action", choices=["sync", "ingest", "yaml", "list", "reset"], 
                        help="Action to perform: \n"
                             "sync: Run both ingest and yaml sync (atomic)\n"
                             "ingest: Scan folders and add new files to DB\n"
                             "yaml: Update theme_media_resources.yml from DB\n"
                             "list: Print current library status\n"
                             "reset: Wipe and recreate the SFX database")

    args = parser.parse_args()
    manager = SFXLibraryManager()

    if args.action == "sync":
        manager.full_sync()
    elif args.action == "ingest":
        manager.bulk_ingest()
    elif args.action == "yaml":
        manager.sync_to_yaml()
    elif args.action == "list":
        manager.list_library()
    elif args.action == "reset":
        manager.reset_database()

if __name__ == "__main__":
    main()
