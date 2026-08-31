include(joinpath(@__DIR__, "src", "Simulation.jl"))
using .RhythmicSimulation

root = @__DIR__
metrics_path = joinpath(root, "results", "case_metrics.csv")
mkpath(dirname(metrics_path))
open(metrics_path, "w") do io
    println(io, "case,rhythm,contrast,pore_volume_m3,breakthrough_pv,RF_BT,RF_80,RF_90,RF_98,terminal_pv,terminal_RF")
    for (case_name, rhythm, contrast) in default_cases()
        result = run_case(case_name, rhythm, contrast, root)
        println(io, join((result.case_name, result.rhythm, result.contrast,
            result.pore_volume_m3, result.pvb, result.rfb, result.rf80,
            result.rf90, result.rf98, result.terminal_pvi, result.terminal_rf), ','))
        println("Completed $(case_name)")
    end
end
