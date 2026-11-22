# Code behind my MTP report (Jigar K S)

This folder has the code that produced the numbers and figures in my report.
Data and result files are not included.

| Folder | Report part |
|---|---|
| bkt-project/src | Part 1: Basic BKT on ASSISTments 2009-10 |
| ibkt-project/src, fbkt-project/src, sbkt-project/src | Part 1: the three BKT extensions |
| sim | Part 2: the 48-concept simulator and the AUC comparison |
| easy_hard/repo/experiments/difficulty | Part 3: the simulator with the easy-hard rule and the tutor plans (newer than experiments/difficulty) |
| easy_hard/story | Part 3: runs, numbers and figures |
| easy_hard/sweep2 | Part 3: the sweep over settings (it uses its own copy of the simulator, in sweep2/difficulty) |
| easy_hard/report | Turns all results into the report's numbers and figures (build.sh shows the order) |
| calibration_checks | Checks used in the calibration plan |

The Part 2 study with the BKT student is the code on main.
The scripts in easy_hard/report expect the BKT projects and their results in the home folder (for example ~/bkt-project).
The ASSISTments 2009-10 skill-builder data is public.
