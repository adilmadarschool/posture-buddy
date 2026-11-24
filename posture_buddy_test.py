"""Entry point for the 5-second TEST build (PostureBuddyTest.exe)."""
import sys
import posture_buddy

if "--test" not in sys.argv:
    sys.argv.append("--test")
posture_buddy.main()
