import logging
import subprocess
from crontab import CronTab
from .retrieve_data import get_panel_app_list, compare_panel_versions


# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("settings.log"),
        logging.StreamHandler()
    ]
)


def run_update_check():
    """
    Check for updates using compare_panel_versions and update if differences are found.
    """
    try:
        logging.info("Running update check...")
        compare_panel_versions()

        # Check the logs for differences detected
        with open("settings.log", "r") as log_file:
            log_contents = log_file.read()
            if "Differences found between local and API versions:" in log_contents:
                logging.info("Updates detected. Running build_panelApp_database.py...")
                result = subprocess.run(
                    ["python", "build_panelApp_database.py"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    logging.info("Updates applied successfully.")
                else:
                    logging.error(f"Error during update process: {result.stderr}")
            else:
                logging.info("No updates detected. No action needed.")

    except Exception as e:
        logging.error(f"An error occurred during update check: {e}")


def setup_cron(interval, script_path):
    """
    Set up a cron job based on the user's desired interval.
    
    Args:
        interval (str): Interval to run the update check (e.g., "5min", "daily", "weekly").
        script_path (str): Path to the `settings.py` script.
    """
    cron = CronTab(user=True)
    cron.remove_all(comment="PanelApp Updates")  # Remove existing jobs for this script

    # Determine schedule based on interval
    if interval == "5min":
        job = cron.new(command=f"python {script_path} run_now", comment="PanelApp Updates")
        job.minute.every(5)
    elif interval == "daily":
        job = cron.new(command=f"python {script_path} run_now", comment="PanelApp Updates")
        job.setall("0 0 * * *")  # At midnight
    elif interval == "weekly":
        job = cron.new(command=f"python {script_path} run_now", comment="PanelApp Updates")
        job.setall("0 0 * * 0")  # Sunday at midnight
    elif interval == "monthly":
        job = cron.new(command=f"python {script_path} run_now", comment="PanelApp Updates")
        job.setall("0 0 1 * *")  # First day of the month at midnight
    elif interval == "6months":
        job = cron.new(command=f"python {script_path} run_now", comment="PanelApp Updates")
        job.setall("0 0 1 */6 *")  # First day every 6th month at midnight
    elif interval == "yearly":
        job = cron.new(command=f"python {script_path} run_now", comment="PanelApp Updates")
        job.setall("0 0 1 1 *")  # First day of the year at midnight
    else:
        raise ValueError("Invalid interval. Choose from: 5min, daily, weekly, monthly, 6months, yearly.")

    cron.write()
    logging.info(f"Cron job set up successfully for interval: {interval}")


def remove_cron():
    """
    Remove the cron job for PanelApp updates.
    """
    cron = CronTab(user=True)
    cron.remove_all(comment="PanelApp Updates")
    cron.write()
    logging.info("Cron job removed successfully.")


def parse_arguments():
    """
    Parse command-line arguments for the script.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Settings for PanelApp Update Checker.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand for setting the interval
    interval_parser = subparsers.add_parser("interval", help="Set the interval for updates.")
    interval_parser.add_argument("interval", choices=["5min", "daily", "weekly", "monthly", "6months", "yearly"], help="Frequency of updates (e.g., 5min, daily, weekly).")

    # Subcommand for removing the cron job
    subparsers.add_parser("stop_updates", help="Stop scheduled updates.")

    # Subcommand for running the update check immediately
    subparsers.add_parser("run_now", help="Run the update check immediately.")

    return parser.parse_args()


def main():
    """
    Main function to parse arguments and execute the appropriate command.
    """
    args = parse_arguments()

    if args.command == "interval":
        try:
            script_path = __file__  # Path to this script
            setup_cron(args.interval, script_path)
        except ValueError as e:
            logging.error(e)
        except Exception as e:
            logging.error(f"An error occurred while setting up the interval: {e}")

    elif args.command == "stop_updates":
        try:
            remove_cron()
        except Exception as e:
            logging.error(f"An error occurred while stopping updates: {e}")

    elif args.command == "run_now":
        run_update_check()


if __name__ == "__main__":
    main()
