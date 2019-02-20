#!/bin/python3
# -*- coding:utf-8 -*-

class Bucket:
  'bucket which content part of data'
  def __init__(self):
    self.__datadict__ = {}
    self.startflag = 1
    self.endflag = 0
    self.totalkeys = 0
    self.totalmembers = 0

  def set(self,key,count):
    self.__datadict__[key] = count
    self.totalkeys += 1
    self.totalmembers += count


  def setflag(self,startflag = 1):
    self.startflag = startflag
    self.endflag = startflag + self.totalmembers - 1

  def getdict(self):
    return self.__datadict__

  def minkey(self):
    keys = self.__datadict__.keys()
    keys = list(keys)
    return min(keys)

  def maxkey(self):
    keys = self.__datadict__.keys()
    keys = list(keys)
    return max(keys)


  def show(self):
    print( 'startflag:',self.startflag   )
    print( 'endflag:', self.endflag  )
    print( 'totalkeys:',self.totalkeys )
    print( 'totalmembers:',self.totalmembers  )
#    for key in self.__datadict__.keys():
#      print (key,':',self.__datadict__[key] )

class  DataPool:
  'this pool contain all data'
  def __init__(self,minkey,maxkey,startflag = 1,endflag = 0,scale = 10):
    print("init datapool :",  minkey,' -- ',maxkey)
    self.scala = scale
    self.__bucketlist__ = []
    for i in range(self.scala):
      self.__bucketlist__.append(Bucket())
    self.startflag = startflag
    self.endflag = endflag
    self.step = (maxkey - minkey) // self.scala  + 1
    self.startkey = minkey

  def __setflag__(self):
    for i  in range(self.scala):
      currentbucket = self.__bucketlist__[i]
      if i == 0 :
        currentbucket.setflag(self.startflag )
      else:
        preivousbuck = self.__bucketlist__[i - 1]
        currentbucket.setflag( preivousbuck.endflag + 1 )

  def __set__(self,key,count):
    for i in range(self.scala):
      if key < self.startkey + self.step * (i + 1) or (i == self.scala -1) and (  key >=  self.startkey + self.step * (i)  )  :
        currentbucket = self.__bucketlist__[i]
        currentbucket.set(key,count)
        break

  def setbydict(self, datadict):
    for key in datadict.keys():
      self.__set__( key,datadict[key])
#      print('setbydict:',key,'  ',datadict[key])
#      for buck  in  self.__bucketlist__:
#        buck.show()

  def show(self):
    self.__setflag__()
    for i in range(self.scala):
      currentbucket = self.__bucketlist__[i]
      currentbucket.show()


  def getpointbucket(self,point):
    self.__setflag__()
    for i  in range(self.scala):
      currentbucket = self.__bucketlist__[i]
      if point <= currentbucket.endflag:
        return currentbucket
      else:
        pass
    return Bucket()





members = range(10000)
#total of all number
total = len(members)

point = 50
buckets = 10

targetpoint = total * point // 100
targetmember = members[0]


print("total:" + str(len(members)))
tuples = []
memberscount = {}
for member in members:
  count = memberscount[member]  if member in memberscount.keys() else 0
  count += 1
  memberscount[member] = count


keys = memberscount.keys()
minnumber = min(keys)
maxnumber = max(keys)
capacity = (maxnumber - minnumber)//buckets + 1

print ("min:" , minnumber," max:" ,maxnumber)
print ("capacity:" + str(capacity))



datapool = DataPool( minnumber,maxnumber)
datapool.setbydict( memberscount)

currentbucket = datapool.getpointbucket(targetpoint)
#datapool.show()
while(True):

  print(currentbucket.totalmembers,"-------1")
  if currentbucket.totalmembers <=  100:
    data = currentbucket.getdict()
    keys = data.keys()
    keys = list(keys)
    index =targetpoint - currentbucket.startflag + 1
    bucketcount = 0
    print('++++++++++++++++++++++++++++++++++++++++++++++')
    for key in keys:
      bucketcount += data[key]
      if bucketcount >= index:
        targetmember = key
        break
    break
  else :
    datapool = DataPool( currentbucket.minkey(),currentbucket.maxkey(),currentbucket.startflag )
    datapool.setbydict( currentbucket.getdict() )
    currentbucket = datapool.getpointbucket(targetpoint)
    print(currentbucket.totalmembers,"-------2")


print('-----------------------------------------------')
print(currentbucket.startflag)
print(currentbucket.endflag)
print ('targetmember:',targetmember)
#bucket.show()

