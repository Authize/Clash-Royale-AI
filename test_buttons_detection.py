import argparse
import os
import sys
import time


def main():
    parser = argparse.ArgumentParser(description="Test detection of Battle/Claim/OK buttons")
    parser.add_argument("--click", action="store_true", help="Also attempt to click detected button using smart priority")
    args = parser.parse_args()

    # Ensure we can import Actions from the project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from Actions import Actions

    actions = Actions()

    print("\n=== Buttons Detection Test ===")
    print(f"Images search folders: \n - {actions.buttons_images_folder}\n - {actions.images_folder}")

    # Check files presence
    candidates = {
        "battle": ["battle.png", "battlestartbutton.png", "startbattle.png", "battlebutton.png"],
        "claim": ["claim.png", "claimbutton.png", "claim_reward.png", "collect.png"],
        "ok": ["ok.png", "okbutton.png", "okay.png"],
    }
    for name, files in candidates.items():
        resolved = None
        for base in [actions.buttons_images_folder, actions.images_folder]:
            for f in files:
                path = os.path.join(base, f)
                if os.path.exists(path):
                    resolved = path
                    break
            if resolved:
                break
        print(f"- {name.upper()} template: {resolved if resolved else 'NOT FOUND'}")

    print("\nDetecting buttons...")
    battle_found = actions.detect_battle_button()
    print(f"Battle button: {'FOUND' if battle_found else 'not found'}")

    claim_found = actions.detect_claim_button()
    print(f"Claim button: {'FOUND' if claim_found else 'not found'}")

    ok_found = actions.detect_ok_button()
    print(f"OK button: {'FOUND' if ok_found else 'not found'}")

    if args.click:
        print("\nAttempting smart_button_click (priority Battle → Claim → OK)...")
        result = actions.smart_button_click()
        print(f"smart_button_click: {'SUCCESS' if result else 'no buttons clicked'}")
        time.sleep(1)

    print("\nDone.")


if __name__ == "__main__":
    main()


