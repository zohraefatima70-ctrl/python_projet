import copy
import random
from random import randint
# NOTE : DAY_HOURS et DAYS_NUM sont définis dans votre code principal
# DAY_HOURS = 4  # Number of working hours per day
# DAYS_NUM = 5   # Number of days in week

# Schedule chromosome
class Schedule:
    # Initializes chromosomes with configuration block (setup of chromosome)
    def __init__(self, numberOfCrossoverPoints, mutationSize, crossoverProbability, mutationProbability):
        # Number of crossover points of parent's class tables
        self.numberOfCrossoverPoints = numberOfCrossoverPoints
        # Number of classes that is moved randomly by single mutation operation
        self.mutationSize = mutationSize
        # Probability that crossover will occure
        self.crossoverProbability = crossoverProbability
        # Probability that mutation will occure
        self.mutationProbability = mutationProbability
        # Fitness value of chromosome
        self.fitness = 0
        # Time-space slots, one entry represent one hour in one classroom
        self.slots = []
        # Flags of class requirements satisfaction
        self.criteria = []
        self.score = 0
        self.classes = {}
        # Assurez-vous que DAY_HOURS, DAYS_NUM et instance sont définis globalement
        self.slots = ( DAYS_NUM * DAY_HOURS * instance.GetNumberOfRooms() ) * [None]
        self.criteria = (instance.GetNumberOfCourseClasses() * 5 )* [None] 

    # Returns reference to table of classes
    def GetClasses(self):
        return self.classes

    # Imitates copy constructor in C++
    def copy(self, setupOnly):
        #return copy.deepcopy(self)
        c = Schedule(0,0,0,0)
        
        if not setupOnly:
            # copy code
            # Note: Utiliser copy.copy(self.slots) pour éviter des références partagées non désirées
            c.slots = copy.deepcopy(self.slots)
            c.classes = copy.deepcopy(self.classes)

            # copy flags of class requirements
            c.criteria = copy.copy(self.criteria)

            # copy fitness
            c.fitness = self.fitness
        else:
            # reserve space for time-space slots in chromosomes code
            c.slots = ( DAYS_NUM * DAY_HOURS * instance.GetNumberOfRooms() ) * [None]

            # reserve space for flags of class requirements
            c.criteria = ( instance.GetNumberOfCourseClasses() * 5 ) * [None]

        # copy parameters
        c.numberOfCrossoverPoints = self.numberOfCrossoverPoints
        c.mutationSize = self.mutationSize
        c.crossoverProbability = self.crossoverProbability
        c.mutationProbability = self.mutationProbability
        c.score = self.score

        return c
             
    # Makes new chromosome with same setup but with randomly chosen code
    def MakeNewFromPrototype(self):
            # number of time-space slots
            size = len(self.slots)
            # make new chromosome, copy chromosome setup
            newChromosome = self.copy(True)
            # place classes at random position
            c = instance.GetCourseClasses()
            nr = instance.GetNumberOfRooms()
            maxLength = nr * DAY_HOURS * DAYS_NUM
            for it in c:
                # determine random position of class
                dur = it.GetDuration()
                day = randint(0,32767) % DAYS_NUM
                room = randint(0, 32767) % nr
                # Assurez-vous que l'heure de début est valide (DAY_HOURS - dur)
                time = randint(0, 32767) % (DAY_HOURS - dur + 1)
                pos = day * nr * DAY_HOURS + room * DAY_HOURS + time
                
                # fill time-space slots, for each hour of class
                for i in range( dur - 1, -1, -1 ):
                    if newChromosome.slots[ pos + i ] is None:
                        newChromosome.slots[ pos + i ] = [ it ]
                    else:
                        newChromosome.slots[ pos + i ].append( it )

                # insert in class table of chromosome
                newChromosome.classes[ it ] = pos

            newChromosome.CalculateFitness()

            # return smart pointer
            return newChromosome

    # Performes crossover operation using two chromosomes and returns pointer to offspring
    def Crossover(self, parent2):
        # check probability of crossover operation
        if randint(0, 32767) % 100 > self.crossoverProbability:
            # no crossover, just copy first parent
            return self.copy(False)

        # new chromosome object, copy chromosome setup
        n = self.copy(True)

        # number of classes
        size = len(self.classes)
        cp = size * [None]

        # determine crossover point (randomly)
        for i in range( self.numberOfCrossoverPoints, 0, -1 ):
            while 1:
                # Utilisez len(self.classes) au lieu de 'size' car size est fixe.
                # Utilisez une meilleure source de hasard si possible.
                p = randint( 0, 32767 ) % len(self.classes.keys())
                if (not cp[ p ]):
                    cp[ p ] = True
                    break

        j = 0
        
        # make new code by combining parent codes
        first = randint( 0, 1 ) == 0
        
        # NOTE : Cette section de Crossover est complexe en Python à cause de l'itération
        # sur les dictionnaires. J'ai corrigé l'accès aux clés pour assurer la compatibilité.
        
        parent1_keys = list(self.classes.keys())
        parent2_keys = list(parent2.classes.keys())
        
        for i in range( 0, size ):
            current_key = parent1_keys[i] # On assume que les deux parents ont les mêmes clés/cours
            
            if first:
                # insert class from first parent into new chromosome's class table
                it1 = self.classes[ current_key ]
                n.classes[ current_key ] = it1
                
                # all time-space slots of class are copied
                for k in range( current_key.GetDuration() - 1, -1, -1 ):
                    if n.slots[ it1 + k ] is None:
                        n.slots[ it1 + k ] = [ current_key ]
                    else:
                        n.slots[ it1 + k ].append( current_key )
            else:
                # insert class from second parent into new chromosome's class table
                it2 = parent2.classes[ current_key ]
                n.classes[ current_key ] = it2
                
                # all time-space slots of class are copied
                for k in range( current_key.GetDuration() - 1, -1, -1 ):
                    if n.slots[ it2 + k ] is None:
                        n.slots[ it2 + k ] = [ current_key ]
                    else:
                        n.slots[ it2 + k ].append( current_key )

            # crossover point
            if cp[ i ]:
                # change source chromosome
                first = not first

            j = j + 1

        n.CalculateFitness()

        # return smart pointer to offspring
        return n

    # Performs mutation on chromosome
    def Mutation(self):
            # check probability of mutation operation
            if randint(0, 32767) % 100 > self.mutationProbability:
                return None

            # number of classes
            numberOfClasses = len(self.classes)
            # number of time-space slots
            size = len(self.slots)

            class_keys = list(self.classes.keys())
            
            # move selected number of classes at random position
            for i in range(self.mutationSize, 0, -1):
                # select random chromosome for movement
                mpos = randint(0, 32767) % numberOfClasses
                cc1 = class_keys[ mpos ]
                pos1 = self.classes[ cc1 ]

                # determine position of class randomly
                nr = instance.GetNumberOfRooms()
                dur = cc1.GetDuration()
                day = randint(0, 32767) % DAYS_NUM
                room = randint(0, 32767) % nr
                # Assurez-vous que l'heure de début est valide (DAY_HOURS - dur)
                time = randint(0, 32767) % ( DAY_HOURS - dur + 1 )
                pos2 = day * nr * DAY_HOURS + room * DAY_HOURS + time

                # move all time-space slots
                for j in range( dur - 1, -1, -1 ):
                    # remove class hour from current time-space slot
                    c1 = self.slots[ pos1 + j ]
                    # Utilisez une boucle for pour la suppression
                    for k in range( 0, len( c1 ) ):
                        if c1[ k ] == cc1:
                            del c1[ k ]
                            break
                    
                    # Si la liste est vide après la suppression, on la remplace par None
                    if not c1:
                         self.slots[ pos1 + j ] = None

                    # move class hour to new time-space slot
                    if self.slots[ pos2 + j ] is None:
                        self.slots[ pos2 + j ] = [ cc1 ]
                    else:
                        self.slots[ pos2 + j ].append( cc1 )

                # change entry of class table to point to new time-space slots
                self.classes[ cc1 ] = pos2
                
            self.CalculateFitness()

    # Calculates fitness value of chromosome
    def CalculateFitness(self):
        # chromosome's score
        score = 0
        numberOfRooms = instance.GetNumberOfRooms()
        daySize = DAY_HOURS * numberOfRooms

        ci = 0
        
        # --- Variables pour les contraintes douces ---
        group_schedule = {} # { 'GroupeID': { 'JourID': [liste_des_heures_de_début] } }
        professor_schedule = {} # { 'ProfID': { 'JourID': [liste_des_heures_de_début] } }

        # --- Définitions pour le calcul des Soft Constraints ---
        PUNISHMENT_ISOLATED_CLASS = 0.2
        PUNISHMENT_FOR_GAPS = 0.15
        BONUS_CORE_HOURS = 0.1
        PUNISHMENT_EXTREME_HOURS = 0.2
        CORE_START = 1 # Slot 1 (heure de début '1')
        CORE_END = DAY_HOURS - 2 # Slot 2 (heure de fin '2') si DAY_HOURS=4

        # 1. Calcul des contraintes DURES (Hard Constraints) et Remplissage des données Soft
        for i in self.classes.keys():
            # coordinate of time-space slot
            p = self.classes[ i ]
            day = p // daySize
            time_slot_index = (p % daySize) % DAY_HOURS # L'heure de début comme index
            room_index = (p % daySize) // DAY_HOURS
            
            # --- Remplissage des structures Soft ---
            groups = i.GetGroups()
            professor = i.GetProfessor() 

            for group in groups:
                group_id = group.GetName()
                group_schedule.setdefault(group_id, {}).setdefault(day, []).append(time_slot_index)
            
            prof_id = professor.GetName()
            professor_schedule.setdefault(prof_id, {}).setdefault(day, []).append(time_slot_index)
            # --- Fin du Remplissage ---
            
            dur = i.GetDuration()

            # check for room overlapping of classes
            ro = False
            for j in range( dur - 1, -1, -1 ):
                if self.slots[ p + j ] is not None and len( self.slots[ p + j ] ) > 1:
                    ro = True
                    break

            # on room overlapping
            if not ro:
                score = score + 1

            self.criteria[ ci + 0 ] = not ro
                
            cc = i
            r = instance.GetRoomById( room_index ) # Utilisation de l'index de salle
            # does current room have enough seats
            self.criteria[ ci + 1 ] = r.GetNumberOfSeats() >= cc.GetNumberOfSeats()
            if self.criteria[ ci + 1 ]:
                score = score + 1

            # does current room have computers if they are required
            self.criteria[ ci + 2 ] = ( not cc.IsLabRequired() ) or ( cc.IsLabRequired() and r.IsLab() )
            if self.criteria[ ci + 2 ]:
                score = score + 1

            po = False
            go = False
            # check overlapping of classes for professors and student groups (dans d'autres salles au même moment)
            t = day * daySize + time_slot_index
            
            breakPoint = False
            for k in range( numberOfRooms, 0, -1 ): # Parcourt toutes les salles à la même heure/jour
                if breakPoint == True: break
                
                for l in range( dur - 1, -1, -1 ): # Parcourt la durée du cours
                    if breakPoint == True: break
                    
                    # Index dans le tableau slots pour une autre salle (k) et une heure donnée (l)
                    slot_index_check = day * daySize + (k-1) * DAY_HOURS + time_slot_index + l
                    
                    cl = self.slots[ slot_index_check ] 
                    
                    if cl is not None:
                        for it in cl:
                            if breakPoint == True: break
                            if cc != it:
                                # professor overlaps?
                                if not po and cc.ProfessorOverlaps( it ):
                                    po = True
                                # student group overlaps?
                                if not go and cc.GroupsOverlap( it ):
                                    go = True
                                # both type of overlapping? no need to check more
                                if po and go:
                                    breakPoint = True
                                        
                t = t + DAY_HOURS # Cela semble être une erreur de logique de votre code original
            
            # professors have no overlapping classes?
            if not po:
                score = score + 1
            self.criteria[ ci + 3 ] = not po

            # student groups has no overlapping classes?
            if not go:
                score = score + 1
            self.criteria[ ci + 4 ] = not go

            ci += 5
        
        # --- NOUVELLE SECTION : Contraintes DOUCES (Soft Constraints) ---
        soft_penalty = 0
        soft_bonus = 0

        # SOFT 1 : Étalement des cours par jour pour les GROUPES (Isolé)
        for group_id, daily_schedule in group_schedule.items():
            for day, times in daily_schedule.items():
                if len(times) == 1:
                    soft_penalty += PUNISHMENT_ISOLATED_CLASS

        # SOFT 2 : Minimisation des "trous" pour les GROUPES (Gaps)
        for group_id, daily_schedule in group_schedule.items():
            for day, times in daily_schedule.items():
                if len(times) > 1:
                    min_time = min(times)
                    max_time = max(times)
                    
                    # On calcule le nombre d'heures occupées (durée totale des cours)
                    total_duration = sum(instance.GetCourseClass(t).GetDuration() for t in times)
                    
                    # L'étendue réelle est (max_time - min_time) + durée du dernier cours
                    # Si l'étendue est BEAUCOUP plus grande que la durée totale, il y a des trous.
                    
                    # Simplifié : s'il y a plus de 2 heures libres entre min et max
                    if (max_time - min_time) - (len(times) - 1) > 2:
                        soft_penalty += PUNISHMENT_FOR_GAPS
        
        # SOFT 3 : Préférence d'horaires pour les ENSEIGNANTS
        for prof_id, daily_schedule in professor_schedule.items():
            for day, times in daily_schedule.items():
                if not times: continue
                
                min_time = min(times)
                max_time = max(times)
                
                # Pénalité pour commencer trop tôt (slot 0)
                if min_time < CORE_START:
                     soft_penalty += PUNISHMENT_EXTREME_HOURS
                # Pénalité pour finir trop tard (dernier slot)
                if max_time > CORE_END: 
                     soft_penalty += PUNISHMENT_EXTREME_HOURS
                
                # Bonus pour un travail compact au milieu de la journée
                # Si l'écart est petit et que tous les cours sont dans la fenêtre (CORE_START à CORE_END)
                if (max_time - min_time + 1) == len(times) and min_time >= CORE_START and max_time <= CORE_END:
                     soft_bonus += BONUS_CORE_HOURS

        # Calcul final de la Fitness
        max_hard_score = instance.GetNumberOfCourseClasses() * 5
        total_score = score + soft_bonus - soft_penalty
        
        # Normalisation de la fitness. Nous ajoutons un petit facteur aux contraintes douces
        # pour éviter la division par zéro et pour laisser de la place à l'amélioration.
        soft_factor = len(group_schedule) * PUNISHMENT_ISOLATED_CLASS + len(professor_schedule) * PUNISHMENT_EXTREME_HOURS
        
        self.fitness = total_score / (max_hard_score + soft_factor + 0.001) 
        
        self.score = total_score

    # Returns fitness value of chromosome
    def GetFitness(self):
        return self.fitness