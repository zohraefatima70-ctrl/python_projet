import sqlite3
import bcrypt

DB_NAME = 'university_schedule.db'

# --- 1. FONCTIONS DE BASE ET SETUP ---

def setup():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Activer les clés étrangères
    cursor.execute("PRAGMA foreign_keys = ON;")

    # ------------------ TABLE UTILISATEURS ------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'enseignant', 'etudiant')),
            full_name TEXT
        );
    """)

    # ------------------ TABLE ENSEIGNANTS ------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS instructors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, 
            name TEXT NOT NULL, 
            speciality TEXT,
            unavailable_slots TEXT, 
            active BOOLEAN NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    """)

    # ------------------ TABLE SALLES ------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            equipments TEXT,
            active BOOLEAN NOT NULL DEFAULT 1 CHECK (active IN (0,1))
        );
    """)

    # ------------------ TABLE MATIÈRES ------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT NOT NULL UNIQUE,
            hours_total INTEGER NOT NULL,
            type TEXT NOT NULL,
            required_equipment TEXT
        );
    """)

    # ------------------ TABLE GROUPES ------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            student_count INTEGER NOT NULL,
            filiere TEXT NOT NULL,
            active BOOLEAN NOT NULL DEFAULT 1 CHECK (active IN (0,1))
        );
    """)

    # ------------------ TABLE EMPLOI DU TEMPS ------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            instructor_id INTEGER NOT NULL,
            group_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            day INTEGER NOT NULL,
            start_hour INTEGER NOT NULL,
            duration INTEGER NOT NULL,
            FOREIGN KEY(course_id) REFERENCES subjects(id),
            FOREIGN KEY(instructor_id) REFERENCES instructors(id),
            FOREIGN KEY(group_id) REFERENCES groups(id),
            FOREIGN KEY(room_id) REFERENCES rooms(id)
        );
    """)

    # ------------------ TABLE INDISPONIBILITÉS ENSEIGNANTS ------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teacher_unavailability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instructor_id INTEGER NOT NULL,
            day INTEGER NOT NULL,
            start_hour INTEGER NOT NULL,
            duration INTEGER NOT NULL,
            FOREIGN KEY(instructor_id) REFERENCES instructors(id)
        );
    """)

    # ------------------ TABLE RESERVATIONS ------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instructor_id INTEGER NOT NULL,
            room_id INTEGER,
            group_id INTEGER,
            day INTEGER NOT NULL,
            start_hour INTEGER NOT NULL,
            duration INTEGER NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
            FOREIGN KEY(instructor_id) REFERENCES instructors(id),
            FOREIGN KEY(room_id) REFERENCES rooms(id),
            FOREIGN KEY(group_id) REFERENCES groups(id)
        );
    """)

    # ------------------ RELATION MATIÈRES ↔ GROUPES ------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subject_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            group_id INTEGER NOT NULL,
            UNIQUE(subject_id, group_id), -- Assure qu'une relation est unique
            FOREIGN KEY(subject_id) REFERENCES subjects(id),
            FOREIGN KEY(group_id) REFERENCES groups(id)
        );
    """)

    # ------------------ RELATION MATIÈRES ↔ ENSEIGNANTS ------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subject_instructors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            instructor_id INTEGER NOT NULL,
            UNIQUE(subject_id, instructor_id), -- Assure qu'une relation est unique
            FOREIGN KEY(subject_id) REFERENCES subjects(id),
            FOREIGN KEY(instructor_id) REFERENCES instructors(id)
        );
    """)

    # ------------------ ADMIN PAR DÉFAUT ------------------
    cursor.execute("SELECT count(*) FROM users WHERE role='admin'")
    if cursor.fetchone()[0] == 0:
        print("Création de l'administrateur par défaut...")
        password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
        cursor.execute("""
            INSERT INTO users (username, password, role, full_name)
            VALUES (?, ?, ?, ?)
        """, ("admin", password_hash, "admin", "Administrateur Système"))
        conn.commit()
    
    conn.close()
    print("Base de données initialisée avec succès.")

def getConnection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# --- 2. FONCTIONS DE REMPLISSAGE (INSERTION) ---

def get_user_id_by_username(username):
    conn = getConnection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result['id'] if result else None

def get_id_by_name(table, name_col, name_value):
    conn = getConnection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT id FROM {table} WHERE {name_col} = ?", (name_value,))
    result = cursor.fetchone()
    conn.close()
    return result['id'] if result else None

def insert_user(username, password, role, full_name=None):
    conn = getConnection()
    cursor = conn.cursor()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        cursor.execute("""
            INSERT INTO users (username, password, role, full_name)
            VALUES (?, ?, ?, ?)
        """, (username, password_hash, role, full_name))
        user_id = cursor.lastrowid
        conn.commit()
        # print(f"Utilisateur inséré: {username} ({role}) avec ID: {user_id}")
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def populate_users():
    print("\n--- Remplissage des utilisateurs (users) ---")
    insert_user("pdupont", "passens123", "enseignant", "Pierre Dupont")
    insert_user("mlegrand", "passens456", "enseignant", "Marie Legrand")
    insert_user("cbertrand", "passens789", "enseignant", "Charles Bertrand")
    insert_user("adurand", "passetud1", "etudiant", "Alice Durand")
    insert_user("btessier", "passetud2", "etudiant", "Bruno Tessier")
    print("--- Users remplis. ---")

def insert_instructor(user_id, name, speciality, unavailable_slots="", active=1):
    conn = getConnection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO instructors (user_id, name, speciality, unavailable_slots, active)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, name, speciality, unavailable_slots, active))
        instructor_id = cursor.lastrowid
        conn.commit()
        # print(f"Instructeur inséré: {name} (ID: {instructor_id})")
        return instructor_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def populate_instructors():
    print("\n--- Remplissage des instructeurs (instructors) ---")
    user_id_dupont = get_user_id_by_username("pdupont")
    user_id_legrand = get_user_id_by_username("mlegrand")
    user_id_bertrand = get_user_id_by_username("cbertrand")
    
    if user_id_dupont: insert_instructor(user_id_dupont, "Pierre Dupont", "Génie Logiciel", "Lundi_08-10,Mercredi_14-16")
    if user_id_legrand: insert_instructor(user_id_legrand, "Marie Legrand", "Réseaux et Sécurité", "Mardi_14-16,Jeudi_10-12")
    if user_id_bertrand: insert_instructor(user_id_bertrand, "Charles Bertrand", "Bases de Données", "")
    print("--- Instructors remplis. ---")

def insert_room(name, room_type, capacity, equipments="", active=1):
    conn = getConnection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO rooms (name, type, capacity, equipments, active)
            VALUES (?, ?, ?, ?, ?)
        """, (name, room_type, capacity, equipments, active))
        room_id = cursor.lastrowid
        conn.commit()
        # print(f"Salle insérée: {name} (Capacité: {capacity})")
        return room_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def populate_rooms():
    print("\n--- Remplissage des salles (rooms) ---")
    insert_room("A101", "Cours", 40)
    insert_room("A102", "Cours", 50)
    insert_room("B201", "Cours", 30)
    insert_room("LABO_INF01", "Labo Informatique", 25, "PC fixes, Projecteur")
    insert_room("AMPHI_MAGNA", "Amphithéâtre", 150, "Sono, Vidéoprojecteur")
    print("--- Rooms remplis. ---")

def insert_subject(name, code, hours_total, subject_type, required_equipment=""):
    conn = getConnection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO subjects (name, code, hours_total, type, required_equipment)
            VALUES (?, ?, ?, ?, ?)
        """, (name, code, hours_total, subject_type, required_equipment))
        subject_id = cursor.lastrowid
        conn.commit()
        # print(f"Matière insérée: {name} ({code})")
        return subject_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def populate_subjects():
    print("\n--- Remplissage des matières (subjects) ---")
    insert_subject("Introduction au Génie Logiciel", "GL-M101", 30, "CM")
    insert_subject("Algorithmique Avancée", "AA-M102", 40, "CM")
    insert_subject("TD Bases de Données", "BD-T201", 20, "TD")
    insert_subject("TD Réseaux", "RS-T202", 20, "TD")
    insert_subject("TP Programmation Python", "PP-P301", 30, "TP", "PC fixes")
    insert_subject("TP Cybersécurité", "CS-P302", 30, "TP", "PC fixes, Réseau isolé")
    print("--- Subjects remplis. ---")

def insert_group(name, student_count, filiere, active=1):
    conn = getConnection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO groups (name, student_count, filiere, active)
            VALUES (?, ?, ?, ?)
        """, (name, student_count, filiere, active))
        group_id = cursor.lastrowid
        conn.commit()
        # print(f"Groupe inséré: {name}")
        return group_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def populate_groups():
    print("\n--- Remplissage des groupes (groups) ---")
    insert_group("L3_INFO_G1", 35, "Informatique")
    insert_group("L3_INFO_G2", 33, "Informatique")
    insert_group("L3_INFO_TP_A", 18, "Informatique")
    insert_group("L3_INFO_TP_B", 17, "Informatique")
    insert_group("M1_RESEAUX_A", 22, "Réseaux")
    print("--- Groups remplis. ---")

# --- 3. FONCTIONS DE REMPLISSAGE (RELATIONS) ---

def insert_subject_group(subject_id, group_id):
    """ Associe une matière à un groupe. """
    conn = getConnection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO subject_groups (subject_id, group_id)
            VALUES (?, ?)
        """, (subject_id, group_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Relation déjà existante
    finally:
        conn.close()

def populate_subject_groups():
    print("\n--- Remplissage des relations Matières ↔ Groupes ---")
    
    # 1. Récupérer les IDs nécessaires
    group_l3_g1 = get_id_by_name("groups", "name", "L3_INFO_G1")
    group_l3_g2 = get_id_by_name("groups", "name", "L3_INFO_G2")
    group_l3_tpa = get_id_by_name("groups", "name", "L3_INFO_TP_A")
    group_l3_tpb = get_id_by_name("groups", "name", "L3_INFO_TP_B")
    group_m1_a = get_id_by_name("groups", "name", "M1_RESEAUX_A")
    
    sub_gl = get_id_by_name("subjects", "code", "GL-M101")
    sub_aa = get_id_by_name("subjects", "code", "AA-M102")
    sub_bd_td = get_id_by_name("subjects", "code", "BD-T201")
    sub_pp_tp = get_id_by_name("subjects", "code", "PP-P301")
    sub_rs_td = get_id_by_name("subjects", "code", "RS-T202")

    # 2. Associer les matières (CM/TD) aux grands groupes L3 Info
    if sub_gl and group_l3_g1: insert_subject_group(sub_gl, group_l3_g1)
    if sub_gl and group_l3_g2: insert_subject_group(sub_gl, group_l3_g2)
    if sub_aa and group_l3_g1: insert_subject_group(sub_aa, group_l3_g1)
    if sub_aa and group_l3_g2: insert_subject_group(sub_aa, group_l3_g2)

    # 3. Associer les matières (TP) aux sous-groupes L3 Info
    if sub_bd_td and group_l3_tpa: insert_subject_group(sub_bd_td, group_l3_tpa)
    if sub_bd_td and group_l3_tpb: insert_subject_group(sub_bd_td, group_l3_tpb)
    if sub_pp_tp and group_l3_tpa: insert_subject_group(sub_pp_tp, group_l3_tpa)
    if sub_pp_tp and group_l3_tpb: insert_subject_group(sub_pp_tp, group_l3_tpb)

    # 4. Associer les matières (TD) au groupe M1 Réseaux
    if sub_rs_td and group_m1_a: insert_subject_group(sub_rs_td, group_m1_a)
    
    print("--- Relations Matières ↔ Groupes remplies. ---")


def insert_subject_instructor(subject_id, instructor_id):
    """ Associe un enseignant à une matière (expertise). """
    conn = getConnection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO subject_instructors (subject_id, instructor_id)
            VALUES (?, ?)
        """, (subject_id, instructor_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def populate_subject_instructors():
    print("\n--- Remplissage des relations Matières ↔ Enseignants ---")
    
    # 1. Récupérer les IDs nécessaires
    inst_dupont = get_id_by_name("instructors", "name", "Pierre Dupont")
    inst_legrand = get_id_by_name("instructors", "name", "Marie Legrand")
    inst_bertrand = get_id_by_name("instructors", "name", "Charles Bertrand")
    
    sub_gl = get_id_by_name("subjects", "code", "GL-M101")
    sub_aa = get_id_by_name("subjects", "code", "AA-M102")
    sub_bd_td = get_id_by_name("subjects", "code", "BD-T201")
    sub_pp_tp = get_id_by_name("subjects", "code", "PP-P301")
    sub_rs_td = get_id_by_name("subjects", "code", "RS-T202")
    sub_cs_tp = get_id_by_name("subjects", "code", "CS-P302")

    # 2. Associer les experts
    if sub_gl and inst_dupont: insert_subject_instructor(sub_gl, inst_dupont) # Dupont -> Génie Logiciel
    if sub_aa and inst_dupont: insert_subject_instructor(sub_aa, inst_dupont) # Dupont -> Algorithmique
    
    if sub_bd_td and inst_bertrand: insert_subject_instructor(sub_bd_td, inst_bertrand) # Bertrand -> Bases de Données
    if sub_pp_tp and inst_bertrand: insert_subject_instructor(sub_pp_tp, inst_bertrand) # Bertrand -> Python (TP)
    
    if sub_rs_td and inst_legrand: insert_subject_instructor(sub_rs_td, inst_legrand) # Legrand -> Réseaux
    if sub_cs_tp and inst_legrand: insert_subject_instructor(sub_cs_tp, inst_legrand) # Legrand -> Cybersécurité

    # 3. Expertise secondaire
    if sub_pp_tp and inst_dupont: insert_subject_instructor(sub_pp_tp, inst_dupont) # Dupont peut aussi faire du Python
    
    print("--- Relations Matières ↔ Enseignants remplies. ---")


# --- 4. FONCTION MAIN ET EXÉCUTION ---

def main():
    """
    Fonction principale pour initialiser la BD et la remplir avec toutes les données de démonstration.
    """
    # 1. Initialisation (Création des tables et Admin)
    setup() 
    
    # 2. Remplissage des tables principales (doit être fait dans cet ordre)
    populate_users() 
    populate_instructors()
    populate_rooms()
    populate_subjects()
    populate_groups()

    # 3. Remplissage des tables de relations (nécessite les IDs des tables principales)
    populate_subject_groups()
    populate_subject_instructors()

    # --- Vérification (Optionnel mais recommandé) ---
    print("\n\n--- VÉRIFICATION FINALE DES DONNÉES EN BD ---")
    conn = getConnection()
    print(f"\nNombre total d'utilisateurs: {conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]}")
    print(f"Nombre total d'instructeurs: {conn.execute('SELECT COUNT(*) FROM instructors').fetchone()[0]}")
    print(f"Nombre total de matières: {conn.execute('SELECT COUNT(*) FROM subjects').fetchone()[0]}")
    print(f"Nombre total de groupes: {conn.execute('SELECT COUNT(*) FROM groups').fetchone()[0]}")
    print(f"Nombre de relations Matière ↔ Groupe: {conn.execute('SELECT COUNT(*) FROM subject_groups').fetchone()[0]}")
    print(f"Nombre de relations Matière ↔ Enseignant: {conn.execute('SELECT COUNT(*) FROM subject_instructors').fetchone()[0]}")
    
    print("\nBase de données de démonstration entièrement remplie.")
    conn.close()

if __name__ == "__main__":
    main()