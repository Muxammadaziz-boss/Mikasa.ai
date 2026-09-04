import main
print('Starting GUI with error capture...')
try:
    main.gui_ishga_tushir()
    print('✅ GUI started successfully')
except Exception as e:
    print(f'❌ GUI Error: {e}')
    import traceback
    traceback.print_exc()
