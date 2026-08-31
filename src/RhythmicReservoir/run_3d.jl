include(joinpath(@__DIR__, "src", "Simulation.jl"))
using .RhythmicSimulation

root = @__DIR__
grid = (50, 10, 20)
lengths = (500.0, 100.0, 20.0)
metrics_path = joinpath(root, "results_3d", "case_metrics.csv")
mkpath(dirname(metrics_path))

open(metrics_path, "w") do io
    println(io, "case,rhythm,contrast,pore_volume_m3,breakthrough_pv,RF_BT,RF_80,RF_90,RF_98,terminal_pv,terminal_RF")
    for (case_name, rhythm, contrast) in default_cases()[2:end]
        result = run_case(case_name, rhythm, contrast, root;
            grid = grid, lengths = lengths, results_dir = "results_3d")
        println(io, join((result.case_name, result.rhythm, result.contrast,
            result.pore_volume_m3, result.pvb, result.rfb, result.rf80,
            result.rf90, result.rf98, result.terminal_pvi, result.terminal_rf), ','))
        println("Completed 3D $(case_name)")
    end
end
