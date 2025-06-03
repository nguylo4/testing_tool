Public FeatureName() As String
Public featureCount As Long

Sub RunCMDAndGetResponse(ByRef inputCell As Range, sheetName As Worksheet, optional_project As String)
    Dim cmdCommand As String
    Dim shellOutput As String
    Dim shellObject As Object
    Dim execObject As Object
    Dim outputLine As String

    ' L?y l?nh t? ô du?c truy?n vào
    cmdCommand = inputCell.Value

    If cmdCommand = "" Then
        MsgBox "Ô A1 dang tr?ng. Vui ḷng nh?p l?nh CMD.", vbExclamation
        Exit Sub
    End If

    ' T?o d?i tu?ng Shell
    Set shellObject = CreateObject("WScript.Shell")
    Set execObject = shellObject.Exec("cmd /c si viewproject --project " & cmdCommand & optional_project & " --no")

    ' Đ?c toàn b? output
    Do While Not execObject.StdOut.AtEndOfStream
        outputLine = execObject.StdOut.ReadLine
        shellOutput = shellOutput & outputLine & vbCrLf
    Loop

    ' Ghi k?t qu? vào các ô t? A2 tr? xu?ng, m?i ḍng m?t c?m tách thành 3 ô liên ti?p
    Dim outputLines() As String
    Dim i As Integer
    Dim parts() As String
    outputLines = Split(shellOutput, vbCrLf)
    For i = 0 To UBound(outputLines) - 1 ' Lo?i b? ḍng cu?i r?ng
        If Trim(outputLines(i)) <> "" Then
            parts = Split(Application.WorksheetFunction.Trim(outputLines(i)), " ")
            If UBound(parts) = 0 Then
                sheetName.Range("A" & (i + 2)).Value = parts(0)
                sheetName.Range("B" & (i + 2)).Value = ""
                sheetName.Range("C" & (i + 2)).Value = ""
            ElseIf UBound(parts) = 1 Then
                sheetName.Range("A" & (i + 2)).Value = parts(0)
                sheetName.Range("B" & (i + 2)).Value = parts(1)
                sheetName.Range("C" & (i + 2)).Value = ""
            ElseIf UBound(parts) >= 2 Then
                sheetName.Range("A" & (i + 2)).Value = parts(0)
                sheetName.Range("B" & (i + 2)).Value = parts(1)
                sheetName.Range("C" & (i + 2)).Value = parts(2)
            End If
        End If
    Next i
End Sub
Sub CreateSheetIfSubproject(sheetCell As Range)
    Dim sheetName As String
    Dim wsNew As Worksheet
    
    If LCase(sheetCell.Offset(0, 1).Value) = "subproject" Then
        sheetName = sheetCell.Value
        ' L?y ph?n tru?c d?u "/" n?u có
        If InStr(sheetName, "/") > 0 Then
            sheetName = Left(sheetName, InStr(sheetName, "/") - 1)
        End If
        ' Thay th? kư t? không h?p l?
        sheetName = Replace(sheetName, "/", "_")
        sheetName = Replace(sheetName, "\", "_")
        sheetName = Replace(sheetName, "*", "_")
        sheetName = Replace(sheetName, "[", "_")
        sheetName = Replace(sheetName, "]", "_")
        sheetName = Replace(sheetName, "?", "_")
        sheetName = Replace(sheetName, ":", "_")
        sheetName = Replace(sheetName, "'", "_")
        On Error Resume Next
        Set wsNew = ThisWorkbook.Sheets(sheetName)

        If wsNew Is Nothing Then
            Set wsNew = ThisWorkbook.Sheets.Add(After:=ThisWorkbook.Sheets(ThisWorkbook.Sheets.Count))
            wsNew.Name = sheetName
        Else
            wsNew.Cells.Clear ' Xóa toàn b? n?i dung n?u sheet dă t?n t?i
        End If
        featureCount = featureCount + 1
        ReDim Preserve FeatureName(1 To featureCount)
        FeatureName(featureCount) = sheetName
        On Error GoTo 0
    End If
End Sub

Sub Main()
    Dim endrow As Long
    Dim i As Long
    ' G?i macro v?i ô A1 trên Summary
    RunCMDAndGetResponse Summary.Range("A1"), ThisWorkbook.Sheets("Summary"), "project.pj"
    ' T?o các sheet cho t?ng feature
    endrow = Summary.Cells(Summary.Rows.Count, 1).End(xlUp).Row
    For i = 1 To endrow
        CreateSheetIfSubproject Summary.Range("A" & i)
    Next i
    For i = 1 To UBound(FeatureName)
        Dim ws As Worksheet
        Set ws = ThisWorkbook.Sheets(FeatureName(i))
        ws.Range("A1").Value = Summary.Range("A1").Value & FeatureName(i)
        RunCMDAndGetResponse ws.Range("A1"), ws, "/project.pj"
        
        Dim endrow_feature As Long
        endrow_feature = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
        Dim j As Long
        For j = 2 To endrow_feature
            ws.Cells(j, 4).Value = ws.Range("A1").Value & ws.Cells(j, 1).Value
        Next j
    Next i

End Sub









