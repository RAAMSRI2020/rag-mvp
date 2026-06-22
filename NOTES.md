# Starting steps :
    Installed the claude in my machine after getting my project verified by claude ai and followed those steps and mainly executed two steps like :
        claude - set ups the claude code in our local after basic sign ins
        claude doctor -  does the sanity checks like our config things

# Changes in stage 1 :
   It actually removed the duplicate functions available in generator and retriever and ma
   de them available gloablly in intent file to make it modular
   Bugs left : the me context here misclassifies by means of substring matching like that2

# Changes in stage 2 :
   It actually what did is called answer_query from intent which co-ordinates the retriever-top-K in retriever and generate_answer in generator all executes in a sequence
   UI got rewired so that here it just displays the string rather than doing the function calls

# Pile 1 changes :
   Deleted the fake answers for burger and profile answer returned by the old answer
   These are the overfit functions that fakes the users

# Plie 2 Changes :
   chip - strip (parser) : headers in files are not recognised anymore
   Chunker fix (the real unlock) : long turns been splitted into small ones to make detailed snippets
   clean up - removed the dead code turn id  and maxchars is moved to config.py
   