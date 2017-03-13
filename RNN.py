#coding=utf8
"""
@time:2017-3-12
@Author by Guoshun
@version:python3.5
"""
import numpy as np

def lossFun(inputs, targets, hprev):
    xs, hs, ys, ps = {}, {}, {}, {}      #xs --------------- one-hot
    hs[-1] = np.copy(hprev)
    loss = 0
    # forward pass
    for t in range(len(inputs)):
        #one-hot
        xs[t] = np.zeros((vocab_size,1))
        xs[t][inputs[t]] = 1

        hs[t] = np.tanh(np.dot(Wxh,xs[t]) + np.dot(Whh,hs[t-1]) + bh)
        ys[t] = np.dot(Why,hs[t]) + by
        #softmax
        ps[t] = np.exp(ys[t]) / np.sum(np.exp(ys[t]))
        # softmax (cross-entropy loss)
        loss += -np.log(ps[t][targets[t],0])           #get the value of index[targets[t],0]//matrix index
    # backward pass: compute gradients going backwards
    dWxh, dWhh, dWhy = np.zeros_like(Wxh), np.zeros_like(Whh), np.zeros_like(Why)
    dbh, dby = np.zeros_like(bh), np.zeros_like(by)
    dhnext = np.zeros_like(hs[0])
    for t in reversed(range(len(inputs))):
        dy = np.copy(ps[t])
        dy[targets[t]] -= 1 # backprop into y. see http://cs231n.github.io/neural-networks-case-study/#grad if confused here
        dWhy += np.dot(dy, hs[t].T)
        dby += dy
        #y=softmax(wx+b)    dy/dw,dy/db   进行一次更新操作
        dh = np.dot(Why.T, dy) + dhnext # backprop into h
        dhraw = (1 - hs[t] * hs[t]) * dh # backprop through tanh nonlinearity
        dbh += dhraw
        dWxh += np.dot(dhraw, xs[t].T)
        dWhh += np.dot(dhraw, hs[t-1].T)
        dhnext = np.dot(Whh.T, dhraw)
    for dparam in [dWxh,dWhh,dWhy,dbh,dby]:
        np.clip(dparam, -5, 5, out=dparam) # clip to mitigate exploding gradients
    return loss, dWxh, dWhh, dWhy, dbh, dby, hs[len(inputs)-1]

def sample(h, seed_ix, n):
    """
    sample a sequence of integers from the model
    h is memory state, seed_ix is seed letter for first time step
    """
    x = np.zeros((vocab_size, 1))
    x[seed_ix] = 1
    ixes = []
    for t in range(n):
        h = np.tanh(np.dot(Wxh, x) + np.dot(Whh, h) + bh)
        y = np.dot(Why, h) + by
        p = np.exp(y) / np.sum(np.exp(y))
        ix = np.random.choice(range(vocab_size), p=p.ravel())
        x = np.zeros((vocab_size, 1))
        x[ix] = 1
        ixes.append(ix)
    return ixes

if __name__ == '__main__':
    # data I/O
    data = open("input1.txt").read()
    chars = list(set(data))
    data_size,vocab_size= len(data),len(chars)    #vocab_size is the num of input
    print('data has %d characters, %d unique.' % (data_size, vocab_size))
    char_to_ix = {ch:i for i,ch in enumerate(chars)}
    ix_to_char = {i:ch for i,ch in enumerate(chars)}

    # hyperparameters
    hidden_size = 100 # size of hidden layer of neurons
    seq_length = 25 # number of steps to unroll the RNN for/like a batch
    learning_rate = 1e-1
    Wxh = np.random.randn(hidden_size,vocab_size)*0.01
    Whh = np.random.randn(hidden_size, hidden_size)*0.01 # hidden to hidden
    Why = np.random.randn(vocab_size, hidden_size)*0.01 # hidden to output
    bh = np.zeros((hidden_size, 1)) # hidden bias
    by = np.zeros((vocab_size, 1)) # output bias

    n,p = 0,0
    mWxh, mWhh, mWhy = np.zeros_like(Wxh), np.zeros_like(Whh), np.zeros_like(Why)
    mbh, mby = np.zeros_like(bh), np.zeros_like(by) # memory variables for Adagrad
    smooth_loss = -np.log(1.0/vocab_size)*seq_length # loss at iteration 0
    while True:
        # prepare inputs (we're sweeping from left to right in steps seq_length long)
        if p+seq_length+1 >= len(data) or n == 0:
            hprev = np.zeros((hidden_size,1)) # reset RNN memory
            p = 0 # go from start of data
        inputs = [char_to_ix[ch] for ch in data[p:p+seq_length]]
        targets = [char_to_ix[ch] for ch in data[p+1:p+seq_length+1]]
        # sample from the model now and then
        if n % 100 == 0:
            sample_ix = sample(hprev, inputs[0], 200)
            txt = ''.join(ix_to_char[ix] for ix in sample_ix)
            print('----\n %s \n----' % (txt, ))
        loss, dWxh, dWhh, dWhy, dbh, dby, hprev = lossFun(inputs, targets, hprev)    #hprev是前一层的h值
        smooth_loss = smooth_loss * 0.999 + loss * 0.001
        if n % 100 == 0: print('iter %d, loss: %f' % (n, smooth_loss)) # print progress
        # perform parameter update with Adagrad
        # 采用Adagrad自适应梯度下降法,可参看博文：http://blog.csdn.net/danieljianfeng/article/details/42931721
        for param, dparam, mem in zip([Wxh, Whh, Why, bh, by],[dWxh, dWhh, dWhy, dbh, dby],[mWxh, mWhh, mWhy, mbh, mby]):
            mem += dparam * dparam
            param += -learning_rate * dparam / np.sqrt(mem + 1e-8) # adagrad update
        p += seq_length # move data pointer
        n += 1 # iteration counter