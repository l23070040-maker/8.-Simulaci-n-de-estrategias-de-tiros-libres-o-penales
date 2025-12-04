import random
import csv
import os
from datetime import datetime
import argparse
import math

PLAYERS = [
    {"name": "Lionel", "skill": 0.92, "pressure": 0.03},
    {"name": "Rafael", "skill": 0.85, "pressure": 0.04},
    {"name": "Carlos", "skill": 0.78, "pressure": 0.05},
    {"name": "Hector", "skill": 0.74, "pressure": 0.06},
    {"name": "Diego", "skill": 0.70, "pressure": 0.07},
    {"name": "Marco", "skill": 0.68, "pressure": 0.05},
    {"name": "Pablo", "skill": 0.66, "pressure": 0.06},
    {"name": "Andres", "skill": 0.64, "pressure": 0.07},
    {"name": "Javier", "skill": 0.60, "pressure": 0.08},
    {"name": "Luis", "skill": 0.58, "pressure": 0.09}
]

def theoretical_prob(skill, distance, x, z):
    """
    Calcula probabilidad teórica de gol:
    - Aumenta si la habilidad es mayor.
    - Baja con distancia.
    - Baja si el tiro se aleja del centro.
    """
    # spread es una penalización por desviación en x y z
    spread = math.sqrt((x**2)/15 + (z**2)/15)
    base = skill - 0.015 * (distance - 11) - spread
    # garantizar en rango (0.01, 0.99)
    return min(max(base, 0.01), 0.99)

def simulate_player(player, grid_x, grid_z, distances, shots_per_cell):
    results = []
    name = player["name"]
    skill = player["skill"]
    pressure = player["pressure"]

    print(f"\nSimulando jugador: {name} (skill={skill})")

    for dist in distances:
        for x in grid_x:
            for z in grid_z:

                p_teo = theoretical_prob(skill, dist, x, z)
                p_real = p_teo - pressure
                p_real = max(min(p_real, 0.99), 0.01)

                goles = 0

                for _ in range(shots_per_cell):
                    if random.random() < p_real:
                        goles += 1

                results.append({
                    "player": name,
                    "distance": dist,
                    "x": x,
                    "z": z,
                    "p_teorica": round(p_teo, 4),
                    "tiros": shots_per_cell,
                    "goles": goles,
                    "p_empirica": round(goles / shots_per_cell, 4)
                })

    return results

def print_ascii_maps(results, distances, grid_x, grid_z):
    jugadores = set(r["player"] for r in results)

    for dist in distances:
        for jugador in jugadores:
            print(f"\n=== MAPA ASCII — {jugador} — Distancia {dist} m ===")

            header = "z/x | " + "  ".join([f"{x:6.2f}" for x in grid_x])
            print(header)
            print("-" * len(header))

            for z in grid_z:
                row = [f"{z:4.2f} | "]
                for x in grid_x:
                    celdas = [r for r in results if r["player"] == jugador and r["distance"] == dist and r["x"] == x and r["z"] == z]
                    if celdas:
                        val = celdas[0]["p_empirica"] * 100
                        row.append(f"{val:6.1f}")
                    else:
                        row.append("  --- ")
                print(" ".join(row))

def save_csv(filename, data, fieldnames):
    os.makedirs("outputs", exist_ok=True)
    path = os.path.join("outputs", filename)

    with open(path, "w", newline="", encoding="utf8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    return path

# ============================================================
# RANKING FINAL
# ============================================================
def compute_ranking(results):
    ranking = []
    jugadores = set(r["player"] for r in results)

    for j in jugadores:
        subset = [r for r in results if r["player"] == j]
        goals = sum(r["goles"] for r in subset)
        shots = sum(r["tiros"] for r in subset)
        emp_rate = goals / shots
        theor_avg = sum(r["p_teorica"] for r in subset) / len(subset)

        ranking.append({
            "player": j,
            "goles_totales": goals,
            "tiros_totales": shots,
            "tasa_empirica": round(emp_rate, 4),
            "tasa_teorica_prom": round(theor_avg, 4)
        })

    ranking.sort(key=lambda r: r["tasa_empirica"], reverse=True)
    return ranking

# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--shots", type=int, default=80, help="Tiros por celda (por jugador). Por defecto 80.")
    parser.add_argument("--nx", type=int, default=5, help="Número de posiciones horizontales (x).")
    parser.add_argument("--nz", type=int, default=3, help="Número de posiciones verticales (z).")
    parser.add_argument("--dist", type=int, default=11, help="Distancia (m) de tiro. Por defecto 11 (penal).")
    args = parser.parse_args()

    # Generar grilla (x en arco -3.66..3.66, z en 0.5..2.5)
    grid_x = [round(x, 2) for x in
              [(-3.66 + i * (7.32 / (args.nx - 1))) for i in range(args.nx)]]

    grid_z = [round(z, 2) for z in
              [0.5 + i * (2.0 / (args.nz - 1)) for i in range(args.nz)]]

    distances = [args.dist]

    print("\n=== INICIANDO SIMULACIÓN ===")
    print(f"Jugadores: {len(PLAYERS)}")
    print(f"Celdas por distancia: {len(grid_x)} x {len(grid_z)} = {len(grid_x)*len(grid_z)}")
    print(f"Tiros por celda (por jugador): {args.shots}")
    print("------------------------------------")

    # Simulación
    all_results = []
    for p in PLAYERS:
        all_results += simulate_player(p, grid_x, grid_z, distances, args.shots)

    # Ranking
    ranking = compute_ranking(all_results)

    # Guardar CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    det_path = save_csv(f"detalle_{timestamp}.csv", all_results,
                         ["player", "distance", "x", "z", "p_teorica", "tiros", "goles", "p_empirica"])
    rank_path = save_csv(f"ranking_{timestamp}.csv", ranking,
                         ["player", "goles_totales", "tiros_totales", "tasa_empirica", "tasa_teorica_prom"])

    print("\n=== RESULTADOS GUARDADOS ===")
    print(det_path)
    print(rank_path)

    # Imprimir mapas ASCII
    print_ascii_maps(all_results, distances, grid_x, grid_z)

    # Imprimir ranking por consola
    print("\n=== RANKING (CONSOLa) ===")
    for i, r in enumerate(ranking, start=1):
        print(f"{i:2d}. {r['player']:10s} - EmpRate: {r['tasa_empirica']*100:6.2f}%  (goles={r['goles_totales']}, tiros={r['tiros_totales']})")

    print("\n=== TERMINADO ===")

if __name__ == "__main__":
    main()
