module RhythmicSimulation

using DelimitedFiles
using Jutul
using JutulDarcy
import JutulDarcy: PhaseRelativePermeability, ReservoirRelativePermeabilities,
    add_relperm_parameters!, brooks_corey_relperm

export run_case, run_grid_sensitivity, default_cases

const NX, NY, NZ = 50, 1, 20
const LX, LY, LZ = 500.0, 20.0, 20.0
const POROSITY, SWI = 0.20, 0.20
const INJ_RATE_M3_DAY, P_INITIAL_MPA, P_PRODUCER_MPA = 40.0, 20.0, 18.0

default_cases() = [
    ("H-1", :homogeneous, 1.0),
    ("P-2", :positive, 2.0), ("P-5", :positive, 5.0), ("P-10", :positive, 10.0),
    ("R-2", :reverse, 2.0), ("R-5", :reverse, 5.0), ("R-10", :reverse, 10.0),
    ("C-2", :compound, 2.0), ("C-5", :compound, 5.0), ("C-10", :compound, 10.0),
]

function permeability_profile(rhythm::Symbol, contrast::Real, nz::Int = NZ)
    contrast == 1 && return fill(500.0, nz)
    kmin = 1000.0/(1 + contrast)
    kmax = contrast*kmin
    ξ = collect(range(0.0, 1.0, length = nz))
    if rhythm == :positive
        return kmin .+ ξ.*(kmax - kmin)
    elseif rhythm == :reverse
        return kmax .- ξ.*(kmax - kmin)
    elseif rhythm == :compound
        return kmin .+ (1 .- abs.(2 .* ξ .- 1)).*(kmax - kmin)
    else
        error("Unsupported rhythm: $rhythm")
    end
end

function run_grid_sensitivity(root::String)
    Darcy, bar, kg, meter, day = si_units(:darcy, :bar, :kilogram, :meter, :day)
    records = NamedTuple[]
    for (label, nx, nz) in (("coarse", 25, 10), ("base", 50, 20), ("fine", 100, 40))
        profile_md = permeability_profile(:positive, 5.0, nz)
        mesh = reservoir_mesh((nx, 1, nz), (LX*meter, LY*meter, LZ*meter))
        nc = nx*nz
        permeability = zeros(3, nc)
        for k in 1:nz, i in 1:nx
            cell = cell_index(mesh, (i, 1, k)); kh = profile_md[k]*1e-3*Darcy
            permeability[:, cell] .= (kh, kh, 0.10*kh)
        end
        domain = reservoir_domain(mesh, permeability = permeability, porosity = POROSITY)
        injector = setup_vertical_well(domain, 1, 1, name = :Injector)
        producer = setup_vertical_well(domain, nx, 1, name = :Producer)
        rho_w, rho_o = 1000.0*kg/meter^3, 850.0*kg/meter^3
        system = ImmiscibleSystem((AqueousPhase(), LiquidPhase()), reference_densities = [rho_w, rho_o])
        model, parameters = setup_reservoir_model(domain, system, wells = [injector, producer], extra_out = true)
        replace_variables!(reservoir_model(model), RelativePermeabilities = relperm_definition())
        add_relperm_parameters!(reservoir_model(model))
        parameters = setup_parameters(model)
        parameters[:Reservoir][:PhaseViscosities] .= repeat([0.5e-3, 5.0e-3], 1, nc)
        state0 = setup_reservoir_state(model, Pressure = P_INITIAL_MPA*10*bar, Saturations = [SWI, 1-SWI])
        rate = INJ_RATE_M3_DAY*meter^3/day
        forces = setup_reservoir_forces(model, control = Dict(
            :Injector => InjectorControl(TotalRateTarget(rate), [1.0, 0.0], density = rho_w),
            :Producer => ProducerControl(BottomHolePressureTarget(P_PRODUCER_MPA*10*bar)),
        ))
        ws, _ = simulate_reservoir(state0, model, vcat([0.1, 0.9], fill(10.0, 200)).*day,
            parameters = parameters, forces = forces, info_level = -1)
        time_day = ws.time./day; pvi = rate.*ws.time./sum(pore_volume(domain))
        qo = max.(0.0, -ws[:Producer][:orat].*day); qw = max.(0.0, -ws[:Producer][:wrat].*day)
        rf = cumulative_trapezoid(time_day, qo)./(sum(pore_volume(domain))*(1-SWI))
        fw = qw./max.(qo .+ qw, eps()); ix = findfirst(>=(0.05), fw)
        push!(records, (; label, nx, nz, breakthrough_pv = pvi[ix], terminal_rf = rf[end]))
    end
    path = joinpath(root, "results", "grid_sensitivity.csv")
    open(path, "w") do io
        println(io, "grid,nx,ny,nz,breakthrough_pv,terminal_recovery_factor")
        for r in records
            println(io, join((r.label, r.nx, 1, r.nz, r.breakthrough_pv, r.terminal_rf), ','))
        end
    end
    return records
end

function relperm_definition()
    sw = collect(range(0.0, 1.0, length = 201))
    krw_values = brooks_corey_relperm.(sw, n = 2.0, residual = 0.20,
        residual_total = 0.40, kr_max = 0.30)
    kro_values = brooks_corey_relperm.(1 .- sw, n = 2.0, residual = 0.20,
        residual_total = 0.40, kr_max = 1.00)
    krw = PhaseRelativePermeability(sw, krw_values, label = :ow)
    kro = PhaseRelativePermeability(reverse(1 .- sw), reverse(kro_values), label = :ow)
    return ReservoirRelativePermeabilities(w = krw, ow = kro)
end

function cumulative_trapezoid(time, rate)
    total = zeros(length(time))
    for i in 2:length(time)
        total[i] = total[i-1] + 0.5*(rate[i-1] + rate[i])*(time[i] - time[i-1])
    end
    return total
end

function write_matrix(path, data)
    mkpath(dirname(path))
    writedlm(path, data, ',')
end

function write_state_history(path, state0, states, n, nc, time_day, pvi, bar)
    nt = n + 1
    sw_history = Matrix{Float32}(undef, nc, nt)
    pressure_history = Matrix{Float32}(undef, nc, nt)
    sw_history[:, 1] .= state0[:Reservoir][:Saturations][1, :]
    pressure_history[:, 1] .= state0[:Reservoir][:Pressure]./(10*bar)
    for ix in 1:n
        sw_history[:, ix + 1] .= states[ix][:Saturations][1, :]
        pressure_history[:, ix + 1] .= states[ix][:Pressure]./(10*bar)
    end
    open(path, "w") do io
        write(io, Int32(nt)); write(io, Int32(nc))
        write(io, vcat(0.0, time_day)); write(io, vcat(0.0, pvi))
        write(io, sw_history); write(io, pressure_history)
    end
end

function write_terminal_cells(path, mesh, sw, profile_md, nx, ny, nz, lx, ly, lz)
    open(path, "w") do io
        println(io, "i,j,k,x_m,y_m,depth_m,Sw,So,permeability_md")
        for k in 1:nz, j in 1:ny, i in 1:nx
            cell = cell_index(mesh, (i, j, k))
            println(io, join((i, j, k,
                (i - 0.5)*lx/nx, (j - 0.5)*ly/ny, (k - 0.5)*lz/nz,
                sw[cell], 1 - sw[cell], profile_md[k]), ','))
        end
    end
end

function write_summary(path, time_day, pvi, qo, qw, cumulative_oil, cumulative_water, rf, injector_bhp, producer_bhp)
    open(path, "w") do io
        println(io, "time_day,injected_pv,oil_rate_m3_day,water_rate_m3_day,liquid_rate_m3_day,water_cut,cumulative_oil_m3,cumulative_water_m3,recovery_factor,injector_bhp_mpa,producer_bhp_mpa")
        for i in eachindex(time_day)
            ql = qo[i] + qw[i]
            fw = ql > 0 ? qw[i]/ql : 0.0
            println(io, join((time_day[i], pvi[i], qo[i], qw[i], ql, fw,
                cumulative_oil[i], cumulative_water[i], rf[i], injector_bhp[i], producer_bhp[i]), ','))
        end
    end
end

function event_value(pvi, rf, fw, threshold)
    ix = findfirst(>=(threshold), fw)
    return isnothing(ix) ? (missing, missing) : (pvi[ix], rf[ix])
end

function run_case(case_name::String, rhythm::Symbol, contrast::Real, root::String;
        grid = (NX, NY, NZ), lengths = (LX, LY, LZ), results_dir = "results")
    Darcy, bar, kg, meter, day = si_units(:darcy, :bar, :kilogram, :meter, :day)
    nx, ny, nz = grid
    lx, ly, lz = lengths
    profile_md = permeability_profile(rhythm, contrast, nz)
    mesh = reservoir_mesh((nx, ny, nz), (lx*meter, ly*meter, lz*meter))
    nc = nx*ny*nz
    permeability = zeros(3, nc)
    for k in 1:nz, j in 1:ny, i in 1:nx
        cell = cell_index(mesh, (i, j, k))
        kh = profile_md[k]*1e-3*Darcy
        permeability[:, cell] .= (kh, kh, 0.10*kh)
    end
    domain = reservoir_domain(mesh, permeability = permeability, porosity = POROSITY)
    well_j = cld(ny, 2)
    injector = setup_vertical_well(domain, 1, well_j, name = :Injector)
    producer = setup_vertical_well(domain, nx, well_j, name = :Producer)

    rho_w, rho_o = 1000.0*kg/meter^3, 850.0*kg/meter^3
    system = ImmiscibleSystem((AqueousPhase(), LiquidPhase()), reference_densities = [rho_w, rho_o])
    model, parameters = setup_reservoir_model(domain, system, wells = [injector, producer], extra_out = true)
    rmodel = reservoir_model(model)
    replace_variables!(rmodel, RelativePermeabilities = relperm_definition())
    add_relperm_parameters!(rmodel)
    parameters = setup_parameters(model)
    parameters[:Reservoir][:PhaseViscosities] .= repeat([0.5e-3, 5.0e-3], 1, nc)

    p0 = P_INITIAL_MPA*10*bar
    state0 = setup_reservoir_state(model, Pressure = p0, Saturations = [SWI, 1 - SWI])
    timesteps = vcat([0.1, 0.9], fill(10.0, 200)).*day
    rate = INJ_RATE_M3_DAY*meter^3/day
    controls = Dict(
        :Injector => InjectorControl(TotalRateTarget(rate), [1.0, 0.0], density = rho_w),
        :Producer => ProducerControl(BottomHolePressureTarget(P_PRODUCER_MPA*10*bar)),
    )
    forces = setup_reservoir_forces(model, control = controls)
    well_solutions, states = simulate_reservoir(state0, model, timesteps,
        parameters = parameters, forces = forces, info_level = -1)

    n = min(length(well_solutions.time), length(states))
    time_day = well_solutions.time[1:n]./day
    pore_volume_m3 = sum(pore_volume(domain))
    pvi = rate.*well_solutions.time[1:n]./pore_volume_m3
    producer_data = well_solutions[:Producer]
    injector_data = well_solutions[:Injector]
    oil_rate = max.(0.0, -producer_data[:orat][1:n].*day)
    water_rate = max.(0.0, -producer_data[:wrat][1:n].*day)
    cumulative_oil = cumulative_trapezoid(time_day, oil_rate)
    cumulative_water = cumulative_trapezoid(time_day, water_rate)
    ooip = pore_volume_m3*(1 - SWI)
    rf = cumulative_oil./ooip
    injector_bhp = injector_data[:bhp][1:n]./(10*bar)
    producer_bhp = producer_data[:bhp][1:n]./(10*bar)
    water_cut = water_rate./max.(oil_rate .+ water_rate, eps())
    pvb, rfb = event_value(pvi, rf, water_cut, 0.05)
    _, rf80 = event_value(pvi, rf, water_cut, 0.80)
    _, rf90 = event_value(pvi, rf, water_cut, 0.90)
    terminal_index = something(findfirst(>=(0.98), water_cut), n)
    _, rf98 = event_value(pvi, rf, water_cut, 0.98)

    case_dir = joinpath(root, results_dir, case_name)
    mkpath(case_dir)
    write_state_history(joinpath(case_dir, "state_history.bin"), state0, states, n, nc,
        time_day, pvi, bar)
    write_summary(joinpath(case_dir, "summary.csv"), time_day, pvi, oil_rate, water_rate,
        cumulative_oil, cumulative_water, rf, injector_bhp, producer_bhp)
    write_matrix(joinpath(case_dir, "permeability_md.csv"), reshape(profile_md, nz, 1))
    snapshots = Dict("0p0" => state0[:Reservoir][:Saturations][1, :])
    snapshot_indices = Dict("0p0" => 0)
    for target in (0.1, 0.3, 0.5, 1.0)
        ix = argmin(abs.(pvi .- target))
        label = replace(string(target), "." => "p")
        snapshots[label] = states[ix][:Saturations][1, :]
        snapshot_indices[label] = ix
    end
    snapshots["terminal"] = states[terminal_index][:Saturations][1, :]
    snapshot_indices["terminal"] = terminal_index
    for (label, sw) in snapshots
        sw_xz = permutedims(reshape(sw, nx, ny, nz)[:, well_j, :], (2, 1))
        write_matrix(joinpath(case_dir, "sw_$(label).csv"), sw_xz)
    end
    final_sw = snapshots["terminal"]
    final_so = 1 .- final_sw
    layer_so = [sum(final_so[cell_index(mesh, (i, j, k))] for i in 1:nx, j in 1:ny)/(nx*ny) for k in 1:nz]
    open(joinpath(case_dir, "layer_results.csv"), "w") do io
        println(io, "layer,depth_m,permeability_md,porosity,avg_So")
        for k in 1:nz
            println(io, join((k, (k-0.5)*lz/nz, profile_md[k], POROSITY, layer_so[k]), ','))
        end
    end
    open(joinpath(case_dir, "snapshot_times.csv"), "w") do io
        println(io, "label,time_day,injected_pv")
        for label in ("0p0", "0p1", "0p3", "terminal")
            ix = snapshot_indices[label]
            time = ix == 0 ? 0.0 : time_day[ix]
            injected_pv = ix == 0 ? 0.0 : pvi[ix]
            println(io, join((label, time, injected_pv), ','))
            write_terminal_cells(joinpath(case_dir, "cells_$(label).csv"), mesh, snapshots[label], profile_md,
                nx, ny, nz, lx, ly, lz)
        end
    end
    return (; case_name, rhythm, contrast, pore_volume_m3, pvb, rfb, rf80, rf90, rf98,
        terminal_pvi = pvi[terminal_index], terminal_rf = rf[terminal_index])
end

end
