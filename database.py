import sqlite3
import bcrypt
import os

# Nom du fichier de la base de données
DB_NAME = 'university_schedule.db'

# Constante pour les jours de la semaine (pour l'affichage)
DAYS = {1: "Lundi", 2: "Mardi", 3: "Mercredi", 4: "Jeudi", 5: "Vendredi"}

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
            full_name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
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
            active BOOLEAN NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
            required_equipment TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # ------------------ TABLE GROUPES ------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            student_count INTEGER NOT NULL,
            filiere TEXT NOT NULL,
            active BOOLEAN NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY(course_id) REFERENCES subjects(id),
            FOREIGN KEY(instructor_id) REFERENCES instructors(id),
            FOREIGN KEY(group_id) REFERENCES groups(id),
            FOREIGN KEY(room_id) REFERENCES rooms(id),
            FOREIGN KEY(created_by) REFERENCES users(id)
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
            reason TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            approved_by INTEGER,
            approved_at DATETIME,
            FOREIGN KEY(instructor_id) REFERENCES instructors(id),
            FOREIGN KEY(room_id) REFERENCES rooms(id),
            FOREIGN KEY(group_id) REFERENCES groups(id),
            FOREIGN KEY(approved_by) REFERENCES users(id)
        );
    """)

    # ------------------ RELATION MATIÈRES ↔ GROUPES ------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subject_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            group_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(subject_id, group_id), 
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(subject_id, instructor_id), 
            FOREIGN KEY(subject_id) REFERENCES subjects(id),
            FOREIGN KEY(instructor_id) REFERENCES instructors(id)
        );
    """)

    # ------------------ TRIGGERS POUR updated_at ------------------
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_users_timestamp 
        AFTER UPDATE ON users
        FOR EACH ROW
        BEGIN
            UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_instructors_timestamp 
        AFTER UPDATE ON instructors
        FOR EACH ROW
        BEGIN
            UPDATE instructors SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_rooms_timestamp 
        AFTER UPDATE ON rooms
        FOR EACH ROW
        BEGIN
            UPDATE rooms SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_subjects_timestamp 
        AFTER UPDATE ON subjects
        FOR EACH ROW
        BEGIN
            UPDATE subjects SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_groups_timestamp 
        AFTER UPDATE ON groups
        FOR EACH ROW
        BEGIN
            UPDATE groups SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_timetable_timestamp 
        AFTER UPDATE ON timetable
        FOR EACH ROW
        BEGIN
            UPDATE timetable SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_teacher_unavailability_timestamp 
        AFTER UPDATE ON teacher_unavailability
        FOR EACH ROW
        BEGIN
            UPDATE teacher_unavailability SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_reservations_timestamp 
        AFTER UPDATE ON reservations
        FOR EACH ROW
        BEGIN
            UPDATE reservations SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
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
    print("Base de données initialisée avec succès (avec timestamps).")

def getConnection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row 
    return conn

# --- 2. FONCTIONS UTILITAIRES DE RÉCUPÉRATION D'ID ---

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

# --- 3. FONCTIONS D'INSERTION SPÉCIFIQUES ---

# --- USERS ---
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

# --- INSTRUCTORS ---
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
        print(f"Instructeur inséré: {name} (ID: {instructor_id})")
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

# --- ROOMS ---
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
        print(f"Salle insérée: {name} (Capacité: {capacity})")
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

# --- SUBJECTS ---
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
        print(f"Matière insérée: {name} ({code})")
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

# --- GROUPS ---
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
        print(f"Groupe inséré: {name}")
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

# --- RELATIONS (JOINTURES) ---

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
        return False 
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

    # CM/TD pour L3 G1 & G2
    if sub_gl and group_l3_g1: insert_subject_group(sub_gl, group_l3_g1)
    if sub_gl and group_l3_g2: insert_subject_group(sub_gl, group_l3_g2)
    if sub_aa and group_l3_g1: insert_subject_group(sub_aa, group_l3_g1)
    if sub_aa and group_l3_g2: insert_subject_group(sub_aa, group_l3_g2)

    # TP/TD pour sous-groupes L3 Info
    if sub_bd_td and group_l3_tpa: insert_subject_group(sub_bd_td, group_l3_tpa)
    if sub_bd_td and group_l3_tpb: insert_subject_group(sub_bd_td, group_l3_tpb)
    if sub_pp_tp and group_l3_tpa: insert_subject_group(sub_pp_tp, group_l3_tpa)
    if sub_pp_tp and group_l3_tpb: insert_subject_group(sub_pp_tp, group_l3_tpb)

    # TD pour M1 Réseaux
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
    
    if sub_bd_td and inst_bertrand: insert_subject_instructor(sub_bd_td, inst_bertrand) 
    if sub_pp_tp and inst_bertrand: insert_subject_instructor(sub_pp_tp, inst_bertrand) 
    
    if sub_rs_td and inst_legrand: insert_subject_instructor(sub_rs_td, inst_legrand) 
    if sub_cs_tp and inst_legrand: insert_subject_instructor(sub_cs_tp, inst_legrand) 

    # Expertise secondaire
    if sub_pp_tp and inst_dupont: insert_subject_instructor(sub_pp_tp, inst_dupont) 
    
    print("--- Relations Matières ↔ Enseignants remplies. ---")

# --- FONCTION CRITIQUE : VÉRIFICATION DE CONFLIT D'HORAIRE ---

def check_conflict(instructor_id, group_id, room_id, day, start_hour, duration):
    conn = getConnection()
    cursor = conn.cursor()
    end_hour = start_hour + duration
    
    # 1. Vérification des conflits dans la table 'timetable'
    # Conflit si un enregistrement existant chevauche la nouvelle plage [start_hour, end_hour]
    # (Existing_Start < New_End) AND (New_Start < Existing_End)
    
    query = """
    SELECT 
        'Enseignant' AS type, instructor_id AS entity_id 
    FROM timetable 
    WHERE day = ? AND instructor_id = ? 
    AND (start_hour < ?) AND (? < start_hour + duration)
    UNION ALL
    SELECT 
        'Groupe', group_id
    FROM timetable 
    WHERE day = ? AND group_id = ?
    AND (start_hour < ?) AND (? < start_hour + duration)
    UNION ALL
    SELECT 
        'Salle', room_id
    FROM timetable 
    WHERE day = ? AND room_id = ?
    AND (start_hour < ?) AND (? < start_hour + duration);
    """
    
    params = [
        day, instructor_id, end_hour, start_hour,
        day, group_id, end_hour, start_hour,
        day, room_id, end_hour, start_hour
    ]
    
    cursor.execute(query, params)
    conflict = cursor.fetchone()
    
    if conflict:
        conn.close()
        return f"Conflit d'horaire existant pour l'entité : {conflict['type']} (ID: {conflict['entity_id']})."

    # 2. Vérification des indisponibilités de l'enseignant (teacher_unavailability)
    unavail_query = """
    SELECT 
        id
    FROM teacher_unavailability 
    WHERE instructor_id = ? AND day = ? 
    AND (start_hour < ?) AND (? < start_hour + duration);
    """
    unavail_params = [instructor_id, day, end_hour, start_hour]
    
    cursor.execute(unavail_query, unavail_params)
    unavailability = cursor.fetchone()
    
    conn.close()
    
    if unavailability:
        return "L'enseignant est marqué comme indisponible sur cette plage horaire."
        
    return None # Aucun conflit détecté

# --- TIMETABLE (EMPLOI DU TEMPS) ---

def insert_schedule_slot(course_id, instructor_id, group_id, room_id, day, start_hour, duration, created_by=None):
    # D'abord, vérifier les conflits avant l'insertion
    conflict_message = check_conflict(instructor_id, group_id, room_id, day, start_hour, duration)
    
    if conflict_message:
        print(f"Échec de l'insertion : {conflict_message}")
        return False
        
    conn = getConnection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO timetable (course_id, instructor_id, group_id, room_id, day, start_hour, duration, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (course_id, instructor_id, group_id, room_id, day, start_hour, duration, created_by))
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        print(f"Erreur d'intégrité lors de l'insertion d'un créneau: {e}")
        return False
    finally:
        conn.close()

def populate_timetable():
    print("\n--- Remplissage de l'Emploi du Temps (timetable) ---")

    # Récupération des IDs
    admin_id = get_user_id_by_username("admin")

    inst_dupont = get_id_by_name("instructors", "name", "Pierre Dupont")
    inst_bertrand = get_id_by_name("instructors", "name", "Charles Bertrand")
    inst_legrand = get_id_by_name("instructors", "name", "Marie Legrand")
    
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
    
    room_amphi = get_id_by_name("rooms", "name", "AMPHI_MAGNA")
    room_a101 = get_id_by_name("rooms", "name", "A101")
    room_labo = get_id_by_name("rooms", "name", "LABO_INF01")

    # Jours: Lundi=1, Mardi=2, Mercredi=3, Jeudi=4, Vendredi=5

    # LUNDI (Jour 1)
    if all([sub_gl, inst_dupont, room_amphi]):
        # CM Génie Logiciel (L3 G1 + G2)
        insert_schedule_slot(sub_gl, inst_dupont, group_l3_g1, room_amphi, 1, 10, 2, admin_id) 
        insert_schedule_slot(sub_gl, inst_dupont, group_l3_g2, room_amphi, 1, 10, 2, admin_id) 

    if all([sub_bd_td, inst_bertrand, group_l3_tpa, room_a101]):
        # TD Bases de Données (L3 TP-A)
        insert_schedule_slot(sub_bd_td, inst_bertrand, group_l3_tpa, room_a101, 1, 14, 2, admin_id) 

    # MARDI (Jour 2)
    if all([sub_aa, inst_dupont, room_amphi]):
        # CM Algorithmique (L3 G1 + G2)
        insert_schedule_slot(sub_aa, inst_dupont, group_l3_g1, room_amphi, 2, 8, 2, admin_id)
        insert_schedule_slot(sub_aa, inst_dupont, group_l3_g2, room_amphi, 2, 8, 2, admin_id)

    if all([sub_pp_tp, inst_bertrand, group_l3_tpb, room_labo]):
        # TP Programmation Python (L3 TP-B)
        insert_schedule_slot(sub_pp_tp, inst_bertrand, group_l3_tpb, room_labo, 2, 10, 3, admin_id) 

    # JEUDI (Jour 4)
    if all([sub_rs_td, inst_legrand, group_m1_a, room_a101]):
        # TD Réseaux (M1 Réseaux A)
        insert_schedule_slot(sub_rs_td, inst_legrand, group_m1_a, room_a101, 4, 8, 2, admin_id) 
        
    # Test de conflit (devrait échouer : conflit de salle avec le slot du Lundi 10h-12h)
    if all([sub_aa, inst_legrand, group_m1_a, room_amphi]):
        print("\n--- Test de conflit (devrait échouer) ---")
        insert_schedule_slot(sub_aa, inst_legrand, group_m1_a, room_amphi, 1, 11, 2, admin_id)

    print("\n--- Emploi du Temps rempli avec des créneaux de démonstration. ---")

# --- 4. FONCTION MAIN ET EXÉCUTION ---

def main():
    """
    Fonction principale pour initialiser la BD et la remplir avec toutes les données de démonstration.
    """
    # Optionnel: Supprimer l'ancienne BD pour repartir de zéro à chaque exécution
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print(f"Ancien fichier {DB_NAME} supprimé.")

    # 1. Initialisation (Création des tables et Admin)
    setup() 
    
    # 2. Remplissage des tables principales 
    populate_users() 
    populate_instructors()
    populate_rooms()
    populate_subjects()
    populate_groups()

    # 3. Remplissage des tables de relations 
    populate_subject_groups()
    populate_subject_instructors()
    
    # 4. Remplissage de l'Emploi du Temps (inclut désormais la vérification des conflits)
    populate_timetable()

    # --- VÉRIFICATION FINALE ---
    print("\n\n--- VÉRIFICATION FINALE DES DONNÉES EN BD ---")
    conn = getConnection()
    
    # Affichage des statistiques
    print(f"\nNombre total d'utilisateurs: {conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]}")
    print(f"Nombre total d'instructeurs: {conn.execute('SELECT COUNT(*) FROM instructors').fetchone()[0]}")
    print(f"Nombre total de matières: {conn.execute('SELECT COUNT(*) FROM subjects').fetchone()[0]}")
    print(f"Nombre total de créneaux dans l'emploi du temps: {conn.execute('SELECT COUNT(*) FROM timetable').fetchone()[0]}")
    
    # Affichage détaillé des créneaux avec timestamps
    print("\n--- Créneaux de l'Emploi du Temps Insérés (avec timestamps) ---")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            t.day, t.start_hour, t.duration,
            s.name AS subject_name, 
            i.name AS instructor_name,
            g.name AS group_name,
            r.name AS room_name,
            t.created_at,
            t.updated_at
        FROM timetable t
        JOIN subjects s ON t.course_id = s.id
        JOIN instructors i ON t.instructor_id = i.id
        JOIN groups g ON t.group_id = g.id
        JOIN rooms r ON t.room_id = r.id
        ORDER BY t.day, t.start_hour, g.name
    """)
    
    for row in cursor.fetchall():
        end_hour = row['start_hour'] + row['duration']
        day_name = DAYS.get(row['day'], 'Inconnu')
        print(f"**{day_name} {row['start_hour']:02d}h-{end_hour:02d}h** | Matière: {row['subject_name']} ({row['group_name']}) | Salle: {row['room_name']} | Enseignant: {row['instructor_name']} | Créé: {row['created_at']}")
    
    conn.close() 
    print("\nExécution du script de base de données terminée avec succès.")

if __name__ == "__main__":
    main()