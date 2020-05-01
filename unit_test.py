import mypingsweeper as script

def test_main():
    assert script.main("191.168.1.0/27") == 0
