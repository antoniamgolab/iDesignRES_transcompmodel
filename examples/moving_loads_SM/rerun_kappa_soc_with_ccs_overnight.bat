@echo off
cd /d D:\AntoniaMariaG\Scand_Med_analysis\SM_baby_2\iDesignRES_transcompmodel\examples\moving_loads_SM

echo [%DATE% %TIME%] Re-running KAPPA sensitivity (5 runs, +CCS overnight constraint)...
julia SM_batch_kappa_sensitivity.jl > batch_kappa_sensitivity_v2.log 2>&1

echo [%DATE% %TIME%] Re-running SOC sensitivity (7 runs, +CCS overnight constraint)...
julia SM_batch_soc_sensitivity.jl > batch_soc_sensitivity_v2.log 2>&1

echo [%DATE% %TIME%] ALL DONE
pause
