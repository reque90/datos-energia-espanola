"""
Ejecuta todo el proceso en orden:
1. Descarga de precios de OMIE
2. Descarga de solar y demanda de ESIOS (se salta si no hay token)
3. Limpieza -> CSV horarios + informe de calidad
4. Métricas -> CSV para Power BI

En PyCharm: clic derecho sobre este fichero -> Run 'run_all'.
"""

import download_esios
import download_omie
import clean
import metrics


def main() -> None:
    print("=== 1/4 Descarga OMIE ===")
    download_omie.main()

    print("\n=== 2/4 Descarga ESIOS ===")
    download_esios.main()

    print("\n=== 3/4 Limpieza ===")
    clean.main()

    print("\n=== 4/4 Métricas ===")
    metrics.main()

    print("\nTodo listo. Los CSV para Power BI están en data/processed/")


if __name__ == "__main__":
    main()
