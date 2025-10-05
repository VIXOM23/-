import graphviz

class TreeElem:
    # Классовые переменные - общие для всех экземпляров
    W_i = None
    V_i = None
    V_W = None
    W = None
    max_potential = None
    dot = None
    id_counter = 0  # Исправлено: используем counter вместо id
    
    def __init__(self, weight, score, prev=None, next1=None, next2=None, used=None, label=None):
        # Увеличиваем счетчик и присваиваем ID
        TreeElem.id_counter += 1
        self.idd = TreeElem.id_counter  # Исправлено: используем class counter
        
        self.weight = weight
        self.score = score
        self.prev = prev
        self.next1 = next1
        self.label = label
        self.next2 = next2
        self.used = used
        
        # Вычисляем potential после инициализации основных атрибутов
        self.potential = self.get_potential()
        
        
            
        if self.weight > self.W:
            TreeElem.dot.node(str(self.idd), f'''<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">
  <TR>
    <TD PORT="f0">{self.weight}</TD>
    <TD>{self.score}</TD>
  </TR>
  <TR>
    <TD COLSPAN="2">{self.potential}</TD>
  </TR>
</TABLE>>''', style='filled', fillcolor='deeppink', shape="plaintext")
        
            # Добавляем ребро от родителя, если он есть и это TreeElem
            if prev is not None and hasattr(prev, 'idd'):
                TreeElem.dot.edge(str(prev.idd), str(self.idd), label=self.label)
            self = None
            return
        if not self.max_potential is None:
            if self.potential < self.max_potential:
                TreeElem.dot.node(str(self.idd), f'''<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">
  <TR>
    <TD PORT="f0">{self.weight}</TD>
    <TD>{self.score}</TD>
  </TR>
  <TR>
    <TD COLSPAN="2">{self.potential}</TD>
  </TR>
</TABLE>>''', style='filled', fillcolor='deeppink', shape="plaintext")
        
        # Добавляем ребро от родителя, если он есть и это TreeElem
                if prev is not None and hasattr(prev, 'idd'):
                    TreeElem.dot.edge(str(prev.idd), str(self.idd), label=self.label)
                return
        # Добавляем узел в граф
        TreeElem.dot.node(str(self.idd), f'''<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">
  <TR>
    <TD PORT="f0">{self.weight}</TD>
    <TD>{self.score}</TD>
  </TR>
  <TR>
    <TD COLSPAN="2">{self.potential}</TD>
  </TR>
</TABLE>>''', shape="plaintext")
        
        # Добавляем ребро от родителя, если он есть и это TreeElem
        if prev is not None and hasattr(prev, 'idd'):
            TreeElem.dot.edge(str(prev.idd), str(self.idd), label=self.label)
            
            


        

        if next1 is None:
            index = self.get_next_id()
            self.index = index
            if index != -1:
                new_weight = self.weight + self.W_i[index]
                new_score = self.score + self.V_i[index]
                new_used = self.used + [index] if self.used is not None else [index]
                self.next1 = TreeElem(new_weight, new_score, prev=self, used=new_used, label=f"+{index+1}")
            else: 
                if TreeElem.max_potential is None:
                    TreeElem.max_potential = self.potential
                elif self.potential > TreeElem.max_potential:  # Исправлено: ищем минимальный
                    TreeElem.max_potential = self.potential
        
        if next2 is None and hasattr(self, 'index') and self.index != -1:
            new_used = self.used + [self.index] if self.used is not None else [self.index]
            self.next2 = TreeElem(self.weight, self.score, prev=self, used=new_used, label=f"-{self.index+1}")
        
        

    def get_potential(self):
        if self.W is None or self.W_i is None:
            return 0
        remaining_capacity = self.W - self.weight
        if remaining_capacity <= 0:
            return self.score
        return remaining_capacity * self.get_high_possible_score() + self.score

    def get_high_possible_score(self):
        next_id = self.get_next_id()
        if next_id == -1:
            return 0
        return self.V_W[next_id]

    def get_next_id(self):
        if self.W_i is None or self.V_W is None:
            return -1
        max_index = -1
        for i in range(len(self.V_W)):
            if self.used is not None and i in self.used:
                continue
            if max_index == -1 or self.V_W[i] > self.V_W[max_index]:
                max_index = i
        return max_index

    @classmethod
    def initialize_global_data(cls, Wi, Vi, W):
        cls.W_i = Wi
        cls.V_i = Vi
        cls.W = W
        cls.V_W = W
        cls.max_potential = None
        cls.V_W = [cls.V_i[i] / cls.W_i[i] for i in range(len(cls.W_i))]
        cls.dot = graphviz.Digraph('structs')
        cls.id_counter = 0  # Сбрасываем счетчик

    def display_global_info(self):
        print(f"Instance knows - Weights: {self.W_i}, Values: {self.V_i}")

    def __repr__(self):
        label_str = ""
        used_str = ""
        return f"""{self.weight}  {self.score} {self.label}
        {self.potential:.2f}
        """

if __name__ == "__main__":
# Использование
    TreeElem.initialize_global_data()

    # Создаем корневой элемент (prev=None для корня)
    elem1 = TreeElem(0, 0, prev=None, used=[])

    # Сохраняем и отображаем граф
    TreeElem.dot.render("knapsack_tree", view=True)
    print(f"Max potential: {TreeElem.max_potential}")