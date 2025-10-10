import re
from collections import defaultdict

# Input as a single multiline string
input_text = """
* refactor(user): introduce dao for user commands by @MartinBelthle in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2692
* refactor(ui-common):  improve `SplitView` prop naming and fix decimal precision in localStorage by @hdinia in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2693
* fix(bc): fix a bug when creating new bc by @TheoPascoli in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2699
* feat(ui-matrix): add separate enable flags for `Matrix` filters and resize by @hdinia in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2697
* fix(ui-matrix): enable temporal filters for matrices with fixed column names by @hdinia in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2709
* feat(sts): add new field `allow-overflow` for v9.3+ studies by @MartinBelthle in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2708
* feat(ui): use custom dialog instead of window.confirm for unsaved/ongoing submit warning by @skamril in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2696
* build(ts-gen): bump `timeseries-generation` package by @MartinBelthle in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2712
* feat(ui-launcher): update the dialog by @skamril in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2711
* feat(ui-scenario): filter scenario builder tabs by version by @hdinia in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2698
* feat(ui-studies): add scope filter and a button to show/hide variants by @skamril in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2714
* feat(ui-studies): add folder navigation to individual study views by @hdinia in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2710
* feat(ui-matrix): enable temporal filters where missing by @hdinia in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2715
* fix(ui-studies): minor changes on launch dialog by @skamril in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2716
* feat(ui-matrix): enable filters on `Inflows` matrix by @hdinia in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2717
* fix(ui-tasks): bug admin tasks invisible by @TheoPascoli in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2721
* feat(ui): add threshold-based color for cluster computing indicators by @hdinia in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2722
* feat(ui-debug): include filename in delete confirmation dialogs by @hdinia in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2724
* fix(study): bug deleting raw study with variants by @TheoPascoli in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2720
* fix(upgrade): allow version to be given as 9.2 instead of 920 by @MartinBelthle in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2725
* feat(ui-matrix): recalculate stats based on filtered data when filters active by @hdinia in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2723
* fix(desktop): re-enable watcher config by @smailio in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2731
* feat(xpansion): support reading and editing adequacy criterion inside back-end by @MartinBelthle in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2726
* fix(xpansion): rollback default value for max_iteration by @MartinBelthle in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2733
* feat(launcher)!: add new endpoint for launchers by @TheoPascoli in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2727
* fix(commands): use impersonator instead of id for `user_id` attribute by @MartinBelthle in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2735
* feat(xpansion): support `adequacy_criterion` option inside slurm launcher by @MartinBelthle in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2734
* fix(launcher): change cmd line for local launcher with v9.3 by @MartinBelthle in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2732
* fix(output): remove zipped output after unarchiving for all studies by @MartinBelthle in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2736
* feat(area)!: rename some models by @TheoPascoli in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2695
* feat(ui): add filename to delete confirmation dialogs by @hdinia in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2728
* feat(ui-studies): move favorites studies from Studies sidenav to main app sidebar by @hdinia in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2730
* fix(ui-study): variant not visible after creation by @skamril in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2729
* fix(launcher): remove duplicate launcher id argument and fix API call by @sylvlecl in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2738
* fix(output)!: allow aggregation with columns mismatch by @MartinBelthle in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2718
* feat(ui-studies): make search field manual by @skamril in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2739
* refactor(scenario_builder): introduce dao by @smailio in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2719
* fix(launcher): fix arguments handling in local launcher by @sylvlecl in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2741
* fix(worker): fix archive worker startup by @sylvlecl in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2748
* feat(study_editor): added study author and editor in study metadata by @sylvlecl in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2749
* feat(ui-studies): add study editor field display by @hdinia in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2755
* refactor(ui-studies): update launch dialog by @skamril in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2746
* feat(editor): updating editor name when modifying file studies by @mehdiwahada in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2700
* feat(ui-launcher): add `adequacyCriterions` field by @skamril in https://github.com/AntaresSimulatorTeam/AntaREST/pull/2757
""".strip()

# Categories and their corresponding prefixes
CATEGORY_MAP = {
    "feat": "Features",
    "fix": "Bug fixes",
    "refactor": "Refactorings",
    "perf": "Performances",
    "doc": "Documentation",
    "docs": "Documentation",
    "test": "Tests",
    "build": "Build",
    "chore": "Chore",
}

# Group changes by category
grouped_changes = defaultdict(list)

# Parse each line
for line in input_text.splitlines():
    match = re.match(r"\* (\w+)\(([^)]+)\)!?: (.*?) by @.+ in .+/(\d+)", line.strip())
    if not match:
        continue
    match_breaking_change = re.match(r"\* (\w+)\(([^)]+)\)!: (.*?) by @.+ in .+/(\d+)", line.strip())
    kind, scope, message, pr_number = match.groups()
    category = CATEGORY_MAP.get(kind, "Other")
    grouped_changes[category].append((scope, message, pr_number, bool(match_breaking_change)))

# Output
for category in ["Features", "Bug fixes", "Performances", "Refactorings", "Chore", "Other"]:
    if category in grouped_changes:
        print(f"### {category}\n")
        for scope, message, pr_number, mbr in grouped_changes[category]:
            if mbr:
                badge = " ![Breaking change](https://img.shields.io/badge/-Breaking%20Change-red.svg)"
            else:
                badge = ""
            print(
                f"* **{scope}**: {message} [`{pr_number}`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/{pr_number}){badge}"
            )
        print()


# breaking_changes = []
# # Parse each line
# for line in input_text.splitlines():
#     match = re.match(r"\* (\w+)\(([^)]+)\)!: (.*?) by @.+ in .+/pull/(\d+)", line.strip())
#     if not match:
#         continue
#     kind, scope, message, pr_number = match.groups()
#     category = CATEGORY_MAP.get(kind, "Other")
#     breaking_changes.append((scope, message, pr_number))

# # Output
# if breaking_changes:
#     print(f"### Breaking chages \n")
#     for scope, message, pr_number in breaking_changes:
#         print(f"* **{scope}**: {message} [`{pr_number}`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/{pr_number})")
#     print()
