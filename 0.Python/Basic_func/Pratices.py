fruits = ['orange', 'apple', 'pear', 'banana', 'kiwi', 'apple', 'banana']

a=fruits.count('apple')
print(a)

b=fruits.count('tangerine')
print(b)

c=fruits.index('banana')
print(c)

d=fruits.index('banana', c+1)  # Find next banana starting at position 4
print(d)

fruits.reverse()
print(fruits)

fruits.append('grape')
print(fruits)

fruits.sort()
print(fruits)

fruits.pop()
print(fruits)

print([(x, y) for x in [1,2,3] for y in [3,1,4] if x != y])