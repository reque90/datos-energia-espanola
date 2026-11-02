"""
Ejecuta todo el proceso en orden:
1. Descarga de precios de OMIE
2. Descarga de solar y demanda de Energy-Charts (Fraunhofer ISE)
3. Descarga de la solar diaria oficial de REE (REData), para validar
4. Limpieza -> CSV horarios + validación + informe de calidad
5. Métricas -> CSV para Power BI

Todas las fuentes son públicas y no hace falta registro ni token.

En PyCharm: clic derecho sobre este fichero -> Run 'run_all'.
"""

import download_energy_charts
import download_omie
import download_redata
import clean
import metrics


def main() -> None:
    print("=== 1/5 Descarga OMIE ===")
    download_omie.main()

    print("\n=== 2/5 Descarga Energy-Charts ===")
    download_energy_charts.main()

    print("\n=== 3/5 Descarga REData ===")
    download_redata.main()

    print("\n=== 4/5 Limpieza ===")
    clean.main()

    print("\n=== 5/5 Métricas ===")
    metrics.main()

    print("\nTodo listo. Los CSV para Power BI están en data/processed/")


if __name__ == "__main__":
    main()
