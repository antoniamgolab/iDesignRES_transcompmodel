@echo off
cd /d D:\AntoniaMariaG\Scand_Med_analysis\SM_baby_2\iDesignRES_transcompmodel\examples\moving_loads_SM

echo [%DATE% %TIME%] Starting BATTERY sensitivity (3 runs)...
julia SM_batch_battery_sensitivity.jl > batch_battery_sensitivity.log 2>&1

echo [%DATE% %TIME%] Starting KAPPA sensitivity (5 runs)...
julia SM_batch_kappa_sensitivity.jl > batch_kappa_sensitivity.log 2>&1

echo [%DATE% %TIME%] Starting KSPACE sensitivity (5 runs)...
julia SM_batch_kspace_sensitivity.jl > batch_kspace_sensitivity.log 2>&1

echo [%DATE% %TIME%] Starting SOC sensitivity (7 runs)...
julia SM_batch_soc_sensitivity.jl > batch_soc_sensitivity.log 2>&1

echo [%DATE% %TIME%] ALL DONE
pause
