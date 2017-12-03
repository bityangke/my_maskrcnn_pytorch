import sys
import time
import os
import shutil
import torch
import json, codecs

from colorama import Fore




def create_save_folder(save_path, force=False, ignore_patterns=[]):
    if os.path.exists(save_path):
        print(Fore.RED + save_path + Fore.RESET
              + ' already exists!', file=sys.stderr)
        if not force:
            ans = input('Do you want to overwrite it? [y/N]:')
            if ans not in ('y', 'Y', 'yes', 'Yes'):
                os.exit(1)
        from getpass import getuser
        tmp_path = '/tmp/{}-experiments/{}_{}'.format(getuser(),
                                                      os.path.basename(save_path),
                                                      time.time())
        print('move existing {} to {}'.format(save_path, Fore.RED
                                              + tmp_path + Fore.RESET))
        shutil.copytree(save_path, tmp_path)
        shutil.rmtree(save_path)
    os.makedirs(save_path)
    print('create folder: ' + Fore.GREEN + save_path + Fore.RESET)

    # copy code to save folder
    if save_path.find('debug') < 0:
        shutil.copytree('.', os.path.join(save_path, 'src'), symlinks=True,
                        ignore=shutil.ignore_patterns('*.pyc', '__pycache__',
                                                      '*.path.tar', '*.pth',
                                                      '*.ipynb', '.*', 'data',
                                                      'save', 'save_backup',
                                                      save_path,
                                                      *ignore_patterns))


def adjust_learning_rate(optimizer, lr_init, decay_rate, epoch, num_epochs):
    """Decay Learning rate at 1/2 and 3/4 of the num_epochs"""
    lr = lr_init
    if epoch >= num_epochs * 0.75:
        lr *= decay_rate**2
    elif epoch >= num_epochs * 0.5:
        lr *= decay_rate
    for param_group in optimizer.param_groups:
        param_group['lr'] = lr

def save_(state, save_dir, output, filename='checkpoint.pth.tar'):
    save_path = os.path.join(save_dir, 'default-{}'.format(time.time()))
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    filename = os.path.join(save_path, filename)
    torch.save(state, filename)
    json_file = os.path.join(save_path, 'output.json')
    json.dump(output, codecs.open(json_file, 'w', encoding='utf-8'))

def val_save_(save_dir, output):
    save_path = os.path.join(save_dir, 'val-{}'.format(time.time()))
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    json_file = os.path.join(save_path, 'output.json')
    json.dump(output, codecs.open(json_file, 'w', encoding='utf-8'))

def test_save_(save_dir, output):
    save_path = os.path.join(save_dir, 'test', 'test-{}'.format(time.time()))
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    json_file = os.path.join(save_path, 'output.json')
    json.dump(output, codecs.open(json_file, 'w', encoding='utf-8'))


def get_optimizer(model, args):
    if args.optimizer == 'sgd':
        return torch.optim.SGD(filter(lambda p: p.requires_grad, model.parameters()), args.lr,
                               momentum=args.momentum, nesterov=args.nesterov,
                               weight_decay=args.weight_decay)
    elif args.optimizer == 'rmsprop':
        return torch.optim.RMSprop(filter(lambda p: p.requires_grad, model.parameters()), args.lr,
                                   alpha=args.alpha,
                                   weight_decay=args.weight_decay)
    elif args.optimizer == 'adam':
        return torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), args.lr,
                                betas=(args.beta1, args.beta2),
                                weight_decay=args.weight_decay)
    else:
        raise NotImplementedError


class AverageMeter(object):
    """Computes and stores the average and current value"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count


def error(output, target, topk=(1,)):
    """Computes the error@k for the specified values of k"""
    maxk = max(topk)
    batch_size = target.size(0)

    _, pred = output.topk(maxk, 1, True, True)
    pred = pred.t()
    correct = pred.eq(target.view(1, -1).expand_as(pred))

    res = []
    for k in topk:
        correct_k = correct[:k].view(-1).float().sum(0)
        res.append(100.0 - correct_k.mul_(100.0 / batch_size))
    return res