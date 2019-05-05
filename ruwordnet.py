import os
from copy import deepcopy
import xml.etree.ElementTree as etree

class Sense(object):
    def __init__(self,
                 id,
                 synset_id,
                 synt_type,
                 name,
                 lemma,
                 main_word,
                 poses,
                 meaning):
        """
        Sense class
        """
        self.id = id
        self.synset_id = synset_id
        self.synt_type = synt_type
        self.name = name
        self.lemma = lemma
        self.main_word = main_word
        self.poses = poses
        self.meaning = meaning
        self.composed_of = None
        self.derived_from = None
        
    def __str__(self):
        return str(self.__dict__)
    
        
class Synset(object):
    """
    Synser class
    """
    def __init__(self,
                 id,
                 ruthes_name,
                 definition,
                 part_of_speech
                ):
        self.id = id
        self.part_of_speech = part_of_speech
        self.ruthes_name = ruthes_name
        self.definition = definition
        self.sense_list = []
        self.hypernym_for = []
        self.hyponym_for = []
        self.domain_for = []
        self.antonym = []
        self.pos_synonymy = []
        
    def __str__(self):
        return str(self.__dict__)
        
        
class RuWordNet(object):
    """
    Thesaurus class
    """
    def __init__(self, ruwordnet_path):
        '''
        Thesaurus loading
        Args:
            ruwordnet_path: string, path to thesaurus directory
        '''
        self.ruwordnet_path = ruwordnet_path
        self.id2sense = {}
        self.id2synset = {}
        
        self.__load_senses_and_synsets()
        self.__load_relations()
    

    def __load_senses_and_synsets(self):
        '''
        Load all thesaurus Senses and Synsets.
        '''
        n_senses_path = os.path.join(self.ruwordnet_path, "senses.N.xml")
        v_senses_path = os.path.join(self.ruwordnet_path, "senses.V.xml")
        a_senses_path = os.path.join(self.ruwordnet_path, "senses.A.xml")
        n_synsets_path = os.path.join(self.ruwordnet_path, "synsets.N.xml")
        v_synsets_path = os.path.join(self.ruwordnet_path, "synsets.V.xml")
        a_synsets_path = os.path.join(self.ruwordnet_path, "synsets.A.xml")
        senses_synsets_paths = [n_senses_path, v_senses_path, a_senses_path,
                        n_synsets_path, v_synsets_path, a_synsets_path]
        
        for path_idx, path in enumerate(senses_synsets_paths):
            if not os.path.exists(path):
                print("File {} does not exist! Stop loading RuWordNet".format(path))
                break
            
            print("Loading senses/synsets from {} ...".format(path))
            tree = etree.parse(path)
            root = tree.getroot()
            for value in root:
                value_id = value.attrib["id"]
                if path_idx < 3:
                    assert value_id not in self.id2sense, 'Error: sense id {} already exist'.format(value_id)
                    self.id2sense[value_id] = Sense(**value.attrib)
                else:
                    assert value_id not in self.id2synset, 'Error: synset id {} already exist'.format(value_id)
                    new_synset = Synset(**value.attrib)
                    for sense in value:
                        new_synset.sense_list.append(sense.attrib['id'])
                    self.id2synset[value_id] = new_synset
                    
        self.get_stat()
        

    def __load_relations(self):
        '''
        Load thesaurus relations.
        Only hypernymy loading today
        '''
        n_relations_path = os.path.join(self.ruwordnet_path, "synset_relations.N.xml")
        v_relations_path = os.path.join(self.ruwordnet_path, "synset_relations.V.xml")
        a_relations_path = os.path.join(self.ruwordnet_path, "synset_relations.A.xml")
        
        relations_paths = [n_relations_path, v_relations_path, a_relations_path]
        
        for path_idx, path in enumerate(relations_paths):
            if not os.path.exists(path):
                print("File {} does not exist! Stop loading RuWordNet".format(path))
                break
                
            print("Loading relations from {} ...".format(path))
            tree = etree.parse(path)
            root = tree.getroot()
            for value in root:
                parent_id = value.attrib["parent_id"]
                child_id = value.attrib["child_id"]
                relation_name = value.attrib["name"]
                
                if relation_name == "hypernym" or relation_name == "instance hypernym":
                    self.id2synset[child_id].hypernym_for.append(parent_id)
                    self.id2synset[parent_id].hyponym_for.append(child_id)
    

    def get_synsets(self, part_of_speech=None):
        '''
        Returns all thesaurus synsets
        Args:
            part_of_speech: string, filter by part of speech

        Returns:
            List of thesaurus Synset objects.
        '''
        synsets = []
        for synset in self.id2synset.values():
            if part_of_speech is not None and synset.part_of_speech not in part_of_speech:
                continue
            synsets.append(deepcopy(synset))
        return synsets
                    

    def get_stat(self):
        print("Number of senses: {}".format(len(self.id2sense)))
        print("Number of synsets: {}".format(len(self.id2synset)))
        

    def get_roots(self):
        '''
        Get all root synsets.
        Root synset has no hyperonyms, but has hyponyms

        Returns:
            List of thesaurus root Synset objects.
        '''
        root_synsets = []
        for synset_id, synset in self.id2synset.items():
            if len(synset.hyponym_for) == 0 and len(synset.hypernym_for) != 0:
                root_synsets.append(deepcopy(synset))
        return root_synsets
    

    def get_tree(self, root_synset_id):
        '''
        Get a hyponyms tree for root synset.
        Tree is represented as a hierarchy of dictionaries
        Args:
            root_synset_id: string
        Returns:
            hierarchy of dictionaries from synset id
        '''
        vert_name = self.id2synset[root_synset_id].ruthes_name
        tree = {vert_name:{}}
        for synset_id in self.id2synset[root_synset_id].hypernym_for:
            tree[vert_name].update(self.get_tree(synset_id))
        return tree
    

    def get_child_ids(self, root_synset_id):
        child_ids = []
        for synset_id in self.id2synset[root_synset_id].hypernym_for:
            child_ids += [synset_id] + self.get_child_ids(synset_id)
        return child_ids
    

    def get_synsets_without_relations(self):
        synsets_without_relations = []
        for synset_id, synset in self.id2synset.items():
            if len(synset.hyponym_for) == 0 and len(synset.hypernym_for) == 0:
                synsets_without_relations.append(deepcopy(synset))
        return synsets_without_relations
    

    def get_connect_components(self):
        component_roots = [set([root.id]) for root in self.get_roots()]
        component_set_ids = [set([child_id for root in root_set for child_id in self.get_child_ids(root)])\
                             for root_set in component_roots]
        
        while True:
            new_component_roots = []
            new_component_set_ids = []
        
            for idx_1, component_root_1 in enumerate(component_roots):
                changed = False
                for idx_2, component_root_2 in enumerate(component_roots[idx_1 + 1:]):
                    if len(component_set_ids[idx_1].intersection(component_set_ids[idx_1 + 1 + idx_2])) > 0:

                        new_component_roots.append(component_root_1.union(component_root_2))
                        new_component_roots += component_roots[idx_1 + 1:idx_1 + 1 + idx_2]
                        new_component_roots += component_roots[idx_1 + 1 + idx_2 + 1:]
                        changed = True
                        break
                if changed:
                    break
                new_component_roots.append(component_root_1)
            if len(component_roots) == len(new_component_roots):
                break
            else:
                component_roots = deepcopy(new_component_roots)
                component_set_ids = [
                    set([child_id for root in root_set 
                            for child_id in self.get_child_ids(root)])
                    for root_set in component_roots
                ]
                
        return component_roots