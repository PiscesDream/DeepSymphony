import numpy as np

from DeepSymphony.models.SeqAE import (
    SeqAE, SeqAEHParam)
from DeepSymphony.utils.BatchProcessing import map_dir
from DeepSymphony.utils.MidoCoder import ExampleCoder
from DeepSymphony.utils.MidoWrapper import get_midi, save_midi


if __name__ == '__main__':
    # usage:
    # 1. train a model
    # 2. evaluate it if you want
    # 3. collect the codes
    # 4. generate with the collected code
    mode = 'train'
    # mode = 'eval'
    # mode = 'collect'
    # mode = 'generate'

    hparam = SeqAEHParam(batch_size=64,
                         encoder_cells=[256],
                         decoder_cells=[256],
                         timesteps=200,
                         gen_timesteps=1000,
                         learning_rate=2e-3,
                         iterations=1200,
                         vocab_size=363,
                         debug=False,
                         overwrite_workdir=True)
    model = SeqAE(hparam)
    model.build()
    coder = ExampleCoder()

    if mode in ['train', 'collect', 'eval']:
        data = np.array(map_dir(
            lambda fn: coder.encode(get_midi(fn)),
            './datasets/easymusicnotes/'))

        print(len(data), map(lambda x: len(x), data))
        data = filter(lambda x: len(x) > hparam.timesteps, data)
        print(len(data), map(lambda x: len(x), data))

        def fetch_data(batch_size):
            seqs = []
            for _ in range(batch_size):
                ind = np.random.randint(len(data))
                start = np.random.randint(data[ind].shape[0] -
                                          hparam.timesteps-1)
                seq = data[ind][start:start+hparam.timesteps]
                seqs.append(seq)
            return np.array(seqs)

        if mode == 'train':
            model.train(fetch_data)  # , continued=True)
        if mode == 'collect':
            collection, seqs = model.collect(fetch_data, samples=10)
            np.savez(hparam.workdir+'code_collection.npz',
                     wrapper={'code': collection, 'seqs': seqs})
        if mode == 'eval':
            seqs = fetch_data(hparam.batch_size)
            pred, train_pred = model.eval(seqs)
            np.set_printoptions(linewidth=np.inf)
            for i in range(hparam.batch_size):
                print '='*200
                print seqs[i]
                print train_pred[i]
                print pred[i]

    elif mode == 'generate':
        collection = np.load(hparam.workdir+'code_collection.npz').\
                __getitem__('wrapper').flatten()[0].get('code')
        seqs = np.load(hparam.workdir+'code_collection.npz').\
            __getitem__('wrapper').flatten()[0].get('seqs')

        collection_id = 0
        piece_id = 0

        result = model.generate(collection[collection_id])[piece_id]
        save_midi('example.mid', coder.decode(result, [4]*len(result)))

        truth = seqs[collection_id][piece_id]
        save_midi('truth.mid', coder.decode(truth, [4]*len(result)))

        # how to generate?
        #   encode with 100-length seq, and decode with 1000-length seq
