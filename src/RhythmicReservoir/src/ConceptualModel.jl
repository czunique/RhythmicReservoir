module ConceptualModel

using Jutul
using JutulDarcy

export build_conceptual_model

"""Build the baseline 50×1×20 Cartesian reservoir and two fully completed wells."""
function build_conceptual_model()
    Darcy, bar, _, meter, _ = si_units(:darcy, :bar, :kilogram, :meter, :day)

    nx, ny, nz = 50, 1, 20
    lengths = (500.0, 20.0, 20.0) .* meter
    mesh = reservoir_mesh(:cartesian; nx = nx, ny = ny, nz = nz,
        Lx = lengths[1], Ly = lengths[2], Lz = lengths[3])

    permeability = [500.0, 500.0, 50.0] .* (1e-3 * Darcy)
    domain = reservoir_domain(mesh; permeability = permeability, porosity = 0.20)
    injector = setup_vertical_well(domain, 1, 1, name = :Injector)
    producer = setup_vertical_well(domain, nx, 1, name = :Producer)

    return (; domain, injector, producer, grid = (nx, ny, nz), lengths,
        initial_pressure = 200 * bar, initial_saturations = [0.20, 0.80])
end

end
