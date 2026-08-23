Attribute VB_Name = "modSimulador"
'==============================================================================
' SIMULADOR DE INVESTIMENTOS — MACROS OPCIONAIS
'
' A planilha funciona INTEIRA sem macro nenhuma. Isso é proposital: ambiente
' corporativo de banco costuma bloquear .xlsm, e um simulador que só funciona
' com macro habilitada é um simulador que não funciona.
'
' O que é fórmula (sempre funciona):
'   SIMULAR      — não existe botão: mudou a resposta, os números mudam na hora
'   COMPARAR     — a aba Comparar já lê as seis alternativas mais o imóvel
'   SUGERIR      — o parâmetro "sugestão automática" na aba Consultor
'   VER DETALHES — os botões azuis são hyperlinks internos, não macros
'   VER GRÁFICOS — os gráficos são nativos e acompanham as células
'
' O que só um macro resolve (e por isso está aqui):
'   NOVO CLIENTE      limpar as respostas de uma vez
'   LIMPAR ESCOLHAS   zerar as alternativas escolhidas à mão
'   GERAR RELATÓRIO   exportar a aba Relatório em PDF, já nomeado
'   SALVAR SIMULAÇÃO  guardar o resultado num histórico dentro do arquivo
'   ATUALIZAR DADOS   buscar Selic, CDI, IPCA e TR no Banco Central
'
' Instalação: veja vba/INSTRUCOES.md
'==============================================================================
Option Explicit

Private Const ABA_CLIENTE As String = "Cliente"
Private Const ABA_CONSULTOR As String = "Consultor"
Private Const ABA_PREMISSAS As String = "Premissas"
Private Const ABA_RELATORIO As String = "Relatorio"
Private Const ABA_HISTORICO As String = "Historico"


'------------------------------------------------------------------ NAVEGAÇÃO
Public Sub IrPara(ByVal nomeAba As String)
    On Error Resume Next
    ThisWorkbook.Sheets(nomeAba).Activate
    ThisWorkbook.Sheets(nomeAba).Range("A1").Select
End Sub


'--------------------------------------------------------------- NOVO CLIENTE
Public Sub NovoCliente()
    Dim ws As Worksheet

    If MsgBox("Isso apaga as respostas do cliente atual e volta aos valores padrão." & _
              vbCrLf & vbCrLf & "Quer salvar a simulação atual no histórico antes?", _
              vbYesNoCancel + vbQuestion, "Novo cliente") = vbCancel Then Exit Sub
    If MsgBox("Salvar no histórico?", vbYesNo + vbQuestion, "Novo cliente") = vbYes Then
        SalvarSimulacao
    End If

    Set ws = ThisWorkbook.Sheets(ABA_CLIENTE)
    Application.EnableEvents = False
    ws.Range("F5").Value = "(preencher)"
    ws.Range("F6").Value = Date
    ws.Range("F10").Value = 0
    ws.Range("F12").Value = 0
    ws.Range("F14").Value = "5 a 10 anos"
    ws.Range("F15").Value = 120
    ws.Range("F18").Value = "Talvez"
    ws.Range("F20").Value = "Equilíbrio entre segurança e rentabilidade"
    ws.Range("F22").Value = "Moderado"
    ws.Range("F28").Value = "A"
    Application.EnableEvents = True

    LimparEscolhas
    ws.Activate
    ws.Range("F5").Select
    MsgBox "Pronto para o próximo atendimento.", vbInformation, "Novo cliente"
End Sub


'------------------------------------------------------------ LIMPAR ESCOLHAS
Public Sub LimparEscolhas()
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets(ABA_CONSULTOR)
    ws.Range("C17:C22").ClearContents          ' escolhas manuais das seis alternativas
    ws.Range("D8").Value = "Sim"               ' religa a sugestão automática
End Sub


'------------------------------------------------------------ RELATÓRIO EM PDF
Public Sub GerarRelatorioPDF()
    Dim ws As Worksheet, nomeCliente As String, caminho As String

    Set ws = ThisWorkbook.Sheets(ABA_RELATORIO)
    nomeCliente = CStr(ThisWorkbook.Sheets(ABA_CLIENTE).Range("F5").Value)
    nomeCliente = LimparNome(nomeCliente)
    If Len(nomeCliente) = 0 Then nomeCliente = "cliente"

    caminho = ThisWorkbook.Path
    If Len(caminho) = 0 Then
        MsgBox "Salve a planilha em uma pasta antes de gerar o relatório.", _
               vbExclamation, "Gerar relatório"
        Exit Sub
    End If
    caminho = caminho & Application.PathSeparator & _
              "Simulacao_" & nomeCliente & "_" & Format(Date, "yyyy-mm-dd") & ".pdf"

    On Error GoTo Falhou
    ws.ExportAsFixedFormat Type:=xlTypePDF, Filename:=caminho, _
                           Quality:=xlQualityStandard, OpenAfterPublish:=True
    Exit Sub
Falhou:
    MsgBox "Não foi possível gerar o PDF: " & Err.Description, vbExclamation, "Gerar relatório"
End Sub

Private Function LimparNome(ByVal s As String) As String
    Dim i As Long, c As String, r As String
    For i = 1 To Len(s)
        c = Mid$(s, i, 1)
        If c Like "[A-Za-z0-9 ]" Then r = r & c
    Next i
    LimparNome = Replace(Trim$(r), " ", "_")
End Function


'--------------------------------------------------------- SALVAR NO HISTÓRICO
Public Sub SalvarSimulacao()
    Dim wsH As Worksheet, wsC As Worksheet, wsK As Worksheet, wsM As Worksheet
    Dim lin As Long, i As Long

    Set wsC = ThisWorkbook.Sheets(ABA_CLIENTE)
    Set wsK = ThisWorkbook.Sheets(ABA_CONSULTOR)
    Set wsM = ThisWorkbook.Sheets("Motor")

    On Error Resume Next
    Set wsH = ThisWorkbook.Sheets(ABA_HISTORICO)
    On Error GoTo 0
    If wsH Is Nothing Then
        Set wsH = ThisWorkbook.Sheets.Add(After:=ThisWorkbook.Sheets(ThisWorkbook.Sheets.Count))
        wsH.Name = ABA_HISTORICO
        wsH.Range("A1:L1").Value = Array("Data", "Cliente", "Valor investido", _
            "Aporte mensal", "Prazo (meses)", "Pode retirar antes", "Prioridade", _
            "Perfil", "Cenário", "Alternativa A", "Patrimônio líquido A", "Observações")
        wsH.Range("A1:L1").Font.Bold = True
        wsH.Rows(1).Interior.Color = RGB(11, 59, 96)
        wsH.Range("A1:L1").Font.Color = vbWhite
        wsH.Columns("A:L").ColumnWidth = 18
        wsH.Rows(2).Select
        ActiveWindow.FreezePanes = True
    End If

    lin = wsH.Cells(wsH.Rows.Count, 1).End(xlUp).Row + 1
    wsH.Cells(lin, 1).Value = Now
    wsH.Cells(lin, 1).NumberFormat = "dd/mm/yyyy hh:mm"
    wsH.Cells(lin, 2).Value = wsC.Range("F5").Value
    wsH.Cells(lin, 3).Value = wsC.Range("F10").Value
    wsH.Cells(lin, 4).Value = wsC.Range("F12").Value
    wsH.Cells(lin, 5).Value = wsC.Range("F16").Value
    wsH.Cells(lin, 6).Value = wsC.Range("F18").Value
    wsH.Cells(lin, 7).Value = wsC.Range("F20").Value
    wsH.Cells(lin, 8).Value = wsC.Range("F22").Value
    wsH.Cells(lin, 9).Value = wsK.Range("D5").Value
    wsH.Cells(lin, 10).Value = wsK.Range("H17").Value
    wsH.Cells(lin, 11).Value = Application.WorksheetFunction.Index( _
        wsM.Range("B1:G1000"), wsM.Range("A1:A1000").Find( _
        "Patrimônio líquido no prazo", LookIn:=xlValues, LookAt:=xlWhole).Row, 1)
    For i = 3 To 4
        wsH.Cells(lin, i).NumberFormat = "R$ #,##0"
    Next i
    wsH.Cells(lin, 11).NumberFormat = "R$ #,##0"

    MsgBox "Simulação guardada na aba " & ABA_HISTORICO & " (linha " & lin & ").", _
           vbInformation, "Salvar simulação"
End Sub


'------------------------------------------------------------ ATUALIZAR DADOS
' Busca Selic, CDI, IPCA e TR na API pública do Banco Central e escreve na
' coluna "Base" da aba Premissas. Os cenários Conservador e Otimista continuam
' sendo escolha do consultor: um número observado não vira projeção sozinho.
Public Sub AtualizarIndicadores()
    Dim ws As Worksheet
    Dim selic As Double, cdi As Double, ipca As Double, tr As Double
    Dim ok As Boolean

    Set ws = ThisWorkbook.Sheets(ABA_PREMISSAS)
    If MsgBox("Buscar Selic, CDI, IPCA e TR no Banco Central e gravar na coluna Base?" & _
              vbCrLf & vbCrLf & "Os cenários Conservador e Otimista não são alterados.", _
              vbYesNo + vbQuestion, "Atualizar dados") <> vbYes Then Exit Sub

    Application.StatusBar = "Consultando o Banco Central…"
    ok = True
    selic = UltimoValorSGS(432, 1) / 100
    cdi = UltimoValorSGS(4389, 1) / 100
    ipca = AcumuladoSGS(433, 12)
    tr = AcumuladoSGS(226, 12)
    Application.StatusBar = False

    If selic <= 0 Then ok = False
    If Not ok Then
        MsgBox "Não foi possível consultar o Banco Central. Verifique a conexão ou o proxy da rede." & _
               vbCrLf & "A planilha continua funcionando com os valores atuais.", _
               vbExclamation, "Atualizar dados"
        Exit Sub
    End If

    GravaBase ws, "SELIC", selic
    GravaBase ws, "CDI", cdi
    GravaBase ws, "IPCA", ipca
    GravaBase ws, "TR", tr
    ws.Range("B4").Value = Format(Date, "yyyy-mm-dd")
    ws.Range("B5").Value = Environ$("USERNAME")

    RegistraAtualizacao "Selic, CDI, IPCA e TR", "Banco Central — API SGS"

    MsgBox "Atualizado em " & Format(Date, "dd/mm/yyyy") & ":" & vbCrLf & vbCrLf & _
           "Selic  " & Format(selic, "0.00%") & vbCrLf & _
           "CDI    " & Format(cdi, "0.00%") & vbCrLf & _
           "IPCA   " & Format(ipca, "0.00%") & "  (12 meses)" & vbCrLf & _
           "TR     " & Format(tr, "0.00%") & "  (12 meses)" & vbCrLf & vbCrLf & _
           "Bolsa, câmbio e imóvel continuam como premissa sua — não são dado observado.", _
           vbInformation, "Atualizar dados"
End Sub

Private Sub GravaBase(ws As Worksheet, ByVal codigo As String, ByVal valor As Double)
    Dim achou As Range
    Set achou = ws.Range("B9:B18").Find(codigo, LookIn:=xlValues, LookAt:=xlWhole)
    If achou Is Nothing Then Exit Sub
    ' Só grava onde não há fórmula (CDI e Poupança são calculados).
    If Not ws.Cells(achou.Row, 4).HasFormula Then ws.Cells(achou.Row, 4).Value = valor
End Sub

Private Sub RegistraAtualizacao(ByVal oQue As String, ByVal fonte As String)
    Dim ws As Worksheet, lin As Long
    On Error Resume Next
    Set ws = ThisWorkbook.Sheets("Fontes")
    On Error GoTo 0
    If ws Is Nothing Then Exit Sub
    lin = 18
    Do While Len(ws.Cells(lin, 1).Value) > 0 And lin < 200
        lin = lin + 1
    Loop
    ws.Cells(lin, 1).Value = Date
    ws.Cells(lin, 1).NumberFormat = "dd/mm/yyyy"
    ws.Cells(lin, 2).Value = Environ$("USERNAME")
    ws.Cells(lin, 3).Value = oQue
    ws.Cells(lin, 4).Value = fonte
    ws.Cells(lin, 5).Value = "Atualização automática pelo botão ATUALIZAR DADOS"
End Sub

Private Function ChamaSGS(ByVal serie As Long, ByVal n As Long) As String
    Dim http As Object, url As String
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs." & serie & _
          "/dados/ultimos/" & n & "?formato=json"
    On Error GoTo Falhou
    Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
    http.setTimeouts 15000, 15000, 20000, 30000
    http.Open "GET", url, False
    http.send
    If http.Status = 200 Then ChamaSGS = http.responseText
    Exit Function
Falhou:
    ChamaSGS = ""
End Function

' A resposta é uma lista simples de {"data":"..","valor":".."}. Não vale a pena
' carregar um parser de JSON para isso: basta ler os campos "valor".
Private Function ValoresSGS(ByVal serie As Long, ByVal n As Long) As Variant
    Dim texto As String, partes() As String, i As Long, v() As Double, p As Long
    texto = ChamaSGS(serie, n)
    If Len(texto) = 0 Then Exit Function
    partes = Split(texto, """valor"":""")
    If UBound(partes) < 1 Then Exit Function
    ReDim v(1 To UBound(partes))
    For i = 1 To UBound(partes)
        p = InStr(partes(i), """")
        If p > 1 Then v(i) = CDbl(Replace(Left$(partes(i), p - 1), ".", ","))
    Next i
    ValoresSGS = v
End Function

Private Function UltimoValorSGS(ByVal serie As Long, ByVal n As Long) As Double
    Dim v As Variant
    v = ValoresSGS(serie, n)
    If IsEmpty(v) Then Exit Function
    UltimoValorSGS = v(UBound(v))
End Function

' Compõe as 12 variações mensais numa taxa anual.
Private Function AcumuladoSGS(ByVal serie As Long, ByVal meses As Long) As Double
    Dim v As Variant, i As Long, fator As Double
    v = ValoresSGS(serie, meses)
    If IsEmpty(v) Then Exit Function
    fator = 1
    For i = LBound(v) To UBound(v)
        fator = fator * (1 + v(i) / 100)
    Next i
    AcumuladoSGS = fator - 1
End Function
