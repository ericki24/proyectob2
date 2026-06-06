import psycopg2


import os

# Leer las credenciales desde las variables de entorno del sistema
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "banco_distribuido")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "contraseña_aquí")  

def conectar_db():
    try:
        conexion = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conexion
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None
    


def registrar_cliente_y_cuenta():
    print("\n--- 📝 APERTURA DE CUENTA (Tx 1) ---")
    nombre = input("Nombre del cliente: ")
    dpi = input("DPI del cliente (mínimo 13 dígitos): ")
    telefono = input("Teléfono: ")
    no_cuenta = input("Número de cuenta único (ej: MON-101): ")
    saldo_inicial = float(input("Monto de apertura inicial: "))

    conn = conectar_db()
    if not conn: return
    cursor = conn.cursor()

    try:
        # INICIO DE TRANSACCIÓN MANUAL
        cursor.execute("BEGIN;")
        
        # 1. Insertar Cliente
        cursor.execute(
            "INSERT INTO clientes (nombre, dpi, telefono) VALUES (%s, %s, %s) RETURNING cliente_id;",
            (nombre, dpi, telefono)
        )
        cliente_id = cursor.fetchone()[0]

        # 2. Insertar Cuenta (Asociada al tipo 1: Ahorro por defecto)
        cursor.execute(
            "INSERT INTO cuentas (cliente_id, tipo_id, numero_cuenta, saldo) VALUES (%s, 1, %s, %s);",
            (cliente_id, no_cuenta, saldo_inicial)
        )

        # SI TODO SALE BIEN, SE GUARDAN LOS CAMBIOS COMPLETOS
        conn.commit()
        print("✅ Cliente y cuenta creados con éxito de forma atómica.")
    except Exception as e:
        # SI ALGO FALLA (Ej: DPI menor a 13 por el trigger, o cuenta duplicada), NADA SE GUARDA
        conn.rollback()
        print(f"❌ Error en la transacción. Se aplicó ROLLBACK: {e}")
    finally:
        cursor.close()
        conn.close()

def realizar_transferencia():
    print("\n--- 💸 TRANSFERENCIA ENTRE CUENTAS (Tx 4) ---")
    id_origen = int(input("ID de la Cuenta Origen: "))
    id_destino = int(input("ID de la Cuenta Destino: "))
    monto = float(input("Monto a transferir: "))

    conn = conectar_db()
    if not conn: return
    cursor = conn.cursor()

    try:
        cursor.execute("BEGIN;")

        # 1. Restar de la cuenta origen
        cursor.execute("UPDATE cuentas SET saldo = saldo - %s WHERE cuenta_id = %s;", (monto, id_origen))
        
        # 2. Sumar a la cuenta destino
        cursor.execute("UPDATE cuentas SET saldo = saldo + %s WHERE cuenta_id = %s;", (monto, id_destino))
        
        # 3. Registrar en el historial de transacciones
        cursor.execute(
            "INSERT INTO transacciones (cuenta_origen_id, cuenta_destino_id, tipo_tx_id, monto) VALUES (%s, %s, 3, %s);",
            (id_origen, id_destino, monto)
        )

        conn.commit()
        print("✅ Transferencia realizada con éxito.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Transferencia fallida. Motivo: {e}")
    finally:
        cursor.close()
        conn.close()

def consultar_cuentas():
    print("\n--- 🏦 LISTADO DE CUENTAS EN EL SISTEMA ---")
    conn = conectar_db()
    if not conn: return
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.cuenta_id, cl.nombre, c.numero_cuenta, c.saldo 
        FROM cuentas c 
        JOIN clientes cl ON c.cliente_id = cl.cliente_id;
    """)
    cuentas = cursor.fetchall()
    
    for c in cuentas:
        print(f"ID: {c[0]} | Cliente: {c[1]} | No. Cuenta: {c[2]} | Saldo: Q{c[3]}")
        
    cursor.close()
    conn.close()

def menu():
    while True:
        print("\n=================================")
        print("    SISTEMA GESTIÓN BANCARIA")
        print("=================================")
        print("1. Registrar Cliente y Cuenta Nueva (Tx 1)")
        print("2. Ver Cuentas y Saldos")
        print("3. Realizar Transferencia (Tx 4)")
        print("4. Salir")
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            registrar_cliente_y_cuenta()
        elif opcion == "2":
            consultas_completas = consultar_cuentas()
        elif opcion == "3":
            realizar_transferencia()
        elif opcion == "4":
            print("👋 Saliendo del sistema...")
            break
        else:
            print("⚠️ Opción inválida.")

if __name__ == "__main__":
    menu()