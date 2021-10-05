Antares-Xpansion Changelog
=================
v0.5.0 (10/2021)
--------------------
### Features

 - In benders optimization, master problem .mps is written after each resolution
 - Several investment candidates on the same link  
 - Review of candidates.ini file content (remove of has-link-profile and add enable feature)
 
### Bug fixes

 - option keepMps was still removing some files needed for lp step
 - correction of lp step call if it was the only step asked by user
 - correction of optimization if hurdles cost were used in antares-simulator
 - correction of optimization with binary additionnal constraint between investment candidates

### For developers
 - fix mergemps optimization in debug mode
 - Fix vcpkg on Github Actions
 - Add build cache for Github Actions (Ubuntu only) to speed up the build
 - add sonarcloud analysis
 - use of docker image for build on centos7
 - add read-the-docs documentation
 - generation of pdf user guide from read-the-docs documentation
 - update Cmake to support Xpress on centos7
 
v0.4.0 (07/2021)
-------------------- 
### Features

 - A new multi solver interface is introduced, we no longer use OR-tools
 - The user can choose different solvers
 - The optimality gap is no longer hard-coded and the user can define it in the inputs
 - in case of unfeaseable problems, the program now prints a console and file outputs
 - solver traces can be activated by specific option in benders/bendersmpi console applications
 - Benders console information are now also printed on a specific file
 
### Bug fixes

 - remove erroneus value from the `"problem_status"` entry  of the output json file
 - fix display of overall cost of the best solutions

v0.3.0 (05/2021)
-------------------- 
### Features

 - Add `yearly-weights` file support to define a weight for each antares study MC years
 - Clean of intermediate result file after each simulation step
 - Creation of a Antares-Xpansion version with only one executable
 
### Bug fixes

 - Use study stored in mount network drive 
 - Problem accepting capital letters in candidate areas
 - Small alignment fix in output

v0.2.0 (04/2021)
-------------------- 
### Features

 - Add `update` step to update antares study links with calculated investments
 
### Bug fixes

 - Invalid best iteration display in logs
 - Rounding problem in writing MPS with or-tools
 - Antares-Xpansion can't be launched twice at the same time
 - Windows: Add Microsoft Visual Studio needed redistribuable to installer
 - Linux: wrong antares-solver executable permission and install directory


v0.1.0 (03/2021)
-------------------- 
We’re happy to announce the first open-source version v0.1.0 of Antares-Xpansion.
**Antares-Xpansion** optimizes the installed capacities of an ANTARES study.

The investment decisions are optimized by running ANTARES' simulations iteratively. At each iteration, the installed capacity of the investments are updated, and the simulations are repeated until the total costs have converged to a minimum. The total cost evaluated in this problem are the sum of the **expected operation cost during one year** and **the investment annuity**. 
The user defines investment candidates. Candidate capacities for investment are necessarily links from an ANTARES study.  Investment candidates can be:
 - transmission capacity between two areas
 - thermal generation capacity (located in a virtual node)
 - renewable generation capacity (located in a virtual node)
 - or even flexibilities (located in virtual nodes)

## Notes
This version is only compatible with Antares v8.0 [Antares-Simulator](https://antares-simulator.org). The Antares binaries needed by Antares-Xpansion are available in the installation package of AntaresXpansion

An annual cost, a potential, a link-profile or an already-installed-capacity can be defined for each candidate. Linear constraints between the invested capacities of investment candidates can also be imposed

The optimization is launched from the command prompt, where the details of the iterations are displayed

The optimization can be launched on large studies. Computing performance can be improved by using MPI.
