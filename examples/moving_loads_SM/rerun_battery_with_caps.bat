@echo off
cd /d D:\AntoniaMariaG\Scand_Med_analysis\SM_baby_2\iDesignRES_transcompmodel\examples\moving_loads_SM

echo [%DATE% %TIME%] Re-running BATTERY sensitivity (3 runs, +kappa_pwr +kappa_space +CCS overnight)...
julia SM_batch_battery_sensitivity.jl > batch_battery_sensitivity_v2.log 2>&1

echo [%DATE% %TIME%] DONE
pause
